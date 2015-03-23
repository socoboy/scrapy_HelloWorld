__author__ = 'socoboy'

from scrapy.core.downloader.handlers.http11 import HTTP11DownloadHandler
from selenium import webdriver
from twisted.internet import reactor, threads
from twisted.internet.error import TimeoutError
from time import time
from urlparse import urldefrag


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

        # check download timeout
        self._timeout_cl = reactor.callLater(timeout, d.cancel)
        d.addBoth(self._cb_timeout, url, timeout)
        return d

    def _cb_latency(self, result, request, start_time):
        request.meta['download_latency'] = time() - start_time
        return result

    def _cb_timeout(self, result, url, timeout):
        if self._timeout_cl.active():
            self._timeout_cl.cancel()
            return result
        raise TimeoutError("Selenium Getting %s took longer than %s seconds." % (url, timeout))


def downloadWithSelenium(request, driverName, driverPath):
    driver = create_web_driver(driverName, driverPath)
    page_handler = request.meta.get('page_handler') or None
    return page_handler(driver, request)


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