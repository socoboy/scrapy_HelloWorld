__author__ = 'socoboy'

from scrapy.core.downloader.handlers.http11 import HTTP11DownloadHandler
from scrapy.http.response.html import HtmlResponse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from twisted.internet import reactor, threads
from twisted.internet.error import TimeoutError
from time import time
from urlparse import urldefrag
from twisted.python.threadpool import ThreadPool


class SeleniumDownloadHandler(HTTP11DownloadHandler):
    def __init__(self, settings):
        super(SeleniumDownloadHandler, self).__init__(settings)
        self._enable_driver = settings.getbool('WEB_DRIVER_ENABLED')
        self._driver_name = settings.get('WEB_DRIVER_NAME')
        self._driver_path = settings.get('WEB_DRIVER_PATH')
        selenium_concurrent_request = settings.get('WEB_DRIVER_CONCURRENT_REQUESTS', 16)
        self._thread_pool = ThreadPool(minthreads=selenium_concurrent_request,
                                       maxthreads=selenium_concurrent_request)
        self._thread_pool.start()
        self._driver_timeout = settings.get('WEB_DRIVER_TIMEOUT', 300)

    def download_request(self, request, spider):
        if self._enable_driver and request.meta.get('selenium_needed', False):
            agent = SeleniumAsyncAgent(contextFactory=self._contextFactory,
                                       pool=self._thread_pool,
                                       driverName=self._driver_name,
                                       driverPath=self._driver_path,
                                       connectTimeout=self._driver_timeout)
            return agent.download_request(request)
        else:
            return super(SeleniumDownloadHandler, self).download_request(request, spider)

    def close(self):
        super(SeleniumDownloadHandler, self).close()
        self._thread_pool.stop()


class SeleniumAsyncAgent(object):
    def __init__(self, contextFactory=None, pool=None, driverName=None, driverPath=None, connectTimeout=300):
        self._contextFactory = contextFactory
        self._connectTimeout = connectTimeout
        self._pool = pool
        self._driverName = driverName
        self._driverPath = driverPath

    def download_request(self, request):
        timeout = request.meta.get('web_driver_timeout') or self._connectTimeout
        # request details
        url = urldefrag(request.url)[0]

        # request
        start_time = time()
        d = threads.deferToThreadPool(reactor, self._pool, downloadWithSelenium,
                                      request, self._driverName, self._driverPath, timeout)

        # set download latency
        d.addErrback(self._cb_timeout, url, timeout)
        d.addCallback(self._cb_latency, request, start_time)

        return d

    def _cb_latency(self, result, request, start_time):
        request.meta['download_latency'] = time() - start_time
        return result

    def _cb_timeout(self, error, url, timeout):
        if error.type == TimeoutException:
            raise TimeoutError("Getting %s took longer than %s seconds." % (url, timeout))
        else:
            return error


def downloadWithSelenium(request, driverName, driverPath, timeout):
    # get driver
    driver = create_web_driver(driverName, driverPath)
    driver.set_page_load_timeout(timeout)

    # get page handler
    page_handler = request.meta.get('page_handler') or None

    # process request
    try:
        driver, request = page_handler(driver, request)
    except Exception as e:
        raise e
    else:
        # create response
        response = HtmlResponse(request.url, body=driver.page_source, request=request, encoding='utf8')
    finally:
        driver.quit()
        pass

    return response


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