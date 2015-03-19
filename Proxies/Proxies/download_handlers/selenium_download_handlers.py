__author__ = 'socoboy'

from scrapy.core.downloader.handlers.http11 import HTTP11DownloadHandler
from selenium import webdriver
from twisted.internet import defer, reactor, threads, protocol
from twisted.internet.error import TimeoutError
from time import time
from urlparse import urldefrag
from scrapy.http import Headers
from scrapy.responsetypes import responsetypes
from cStringIO import StringIO
from scrapy.xlib.tx import ResponseDone
from twisted.web.http import PotentialDataLoss


class SeleniumDownloadHandler(HTTP11DownloadHandler):
    def __init__(self, settings):
        super(SeleniumDownloadHandler, self).__init__(settings)
        self._enable_driver = settings.getbool('WEB_DRIVER_ENABLED')
        self._driver_name = settings.get('WEB_DRIVER_NAME')
        self._driver_path = settings.get('WEB_DRIVER_PATH')

    def download_request(self, request, spider):
        if self._enable_driver and request.meta.get('selenium_needed', False):
            agent = SeleniumAsyncAgent(contextFactory=self._contextFactory,
                                       pool=self._pool,
                                       driverName=self._driver_name,
                                       driverPath=self._driver_path)
            return agent.download_request(request)
        else:
            return super(SeleniumDownloadHandler, self).download_request(request, spider)


class SeleniumAsyncAgent(object):
    def __init__(self, contextFactory=None, pool=None, driverName=None, driverPath=None, connectTimeout=300):
        self._contextFactory = contextFactory
        self._connectTimeout = connectTimeout
        self._pool = pool
        self._driverName = driverName
        self._driverPath = driverPath

    def download_request(self, request):
        timeout = request.meta.get('download_timeout') or self._connectTimeout
        # request details
        url = urldefrag(request.url)[0]

        # request
        start_time = time()
        d = threads.deferToThreadPool(reactor, self._pool, downloadWithSelenium,
                                      request, self._driverName, self._driverPath)

        # set download latency
        d.addCallback(self._cb_latency, request, start_time)

        # response body is ready to be consumed
        d.addCallback(self._cb_bodyready, request)
        d.addCallback(self._cb_bodydone, request, url)
        # check download timeout
        self._timeout_cl = reactor.callLater(timeout, d.cancel)
        d.addBoth(self._cb_timeout, request, url, timeout)
        return d

    def _cb_latency(self, result, request, start_time):
        request.meta['download_latency'] = time() - start_time
        return result

    def _cb_bodyready(self, txresponse, request):
        # deliverBody hangs for responses without body
        if txresponse.length == 0:
            return txresponse, '', None

        def _cancel(_):
            txresponse._transport._producer.loseConnection()

        d = defer.Deferred(_cancel)
        txresponse.deliverBody(_ResponseReader(d, txresponse, request))
        return d

    def _cb_bodydone(self, result, request, url):
        txresponse, body, flags = result
        status = int(txresponse.code)
        headers = Headers(txresponse.headers.getAllRawHeaders())
        respcls = responsetypes.from_args(headers=headers, url=url)
        return respcls(url=url, status=status, headers=headers, body=body, flags=flags)

    def _cb_timeout(self, result, request, url, timeout):
        if self._timeout_cl.active():
            self._timeout_cl.cancel()
            return result
        raise TimeoutError("Selenium Getting %s took longer than %s seconds." % (url, timeout))


def downloadWithSelenium(request, driverName, driverPath):
    driver = create_web_driver(driverName, driverPath)
    #pending


def create_web_driver(driverName=None, driverPath=None):
    if driverName == 'phantomjs':
        driver_class = webdriver.PhantomJS
    elif driverName == 'chrome':
        driver_class = webdriver.Chrome
    elif driverName == 'firefox':
        driver_class = webdriver.Firefox
    else:
        driver_class = webdriver.Chrome

    if driverPath:
        driver = driver_class(driverPath)
    else:
        driver = driver_class()

    return driver


class _ResponseReader(protocol.Protocol):

    def __init__(self, finished, txresponse, request):
        self._finished = finished
        self._txresponse = txresponse
        self._request = request
        self._bodybuf = StringIO()

    def dataReceived(self, bodyBytes):
        self._bodybuf.write(bodyBytes)

    def connectionLost(self, reason):
        if self._finished.called:
            return

        body = self._bodybuf.getvalue()
        if reason.check(ResponseDone):
            self._finished.callback((self._txresponse, body, None))
        elif reason.check(PotentialDataLoss):
            self._finished.callback((self._txresponse, body, ['partial']))
        else:
            self._finished.errback(reason)
