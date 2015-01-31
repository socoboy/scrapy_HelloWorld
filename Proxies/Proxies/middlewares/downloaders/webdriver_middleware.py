__author__ = 'socoboy'
from scrapy.exceptions import NotConfigured
from selenium import webdriver


class WebDriverDownloaderMiddleware:
    enabled = False
    driver_name = None
    driver_path = None

    def __init__(self, settings):
        # WEB_DRIVER_ENABLED for enable webdriver downloader
        self.enabled = settings.getbool('WEB_DRIVER_ENABLED')
        self.driver_path = settings.get('WEB_DRIVER_PATH')
        self.driver_name = settings.get('WEB_DRIVER_NAME')
        self._driver = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    @property
    def driver(self):
        if not self.enabled:
            return None

        if not self._driver:
            driver_class = None
            if self.driver_name == 'phantomjs':
                driver_class = webdriver.PhantomJS
            elif self.driver_name == 'chrome':
                driver_class = webdriver.Chrome
            elif self.driver_name == 'firefox':
                driver_class = webdriver.Firefox

            if self.driver_path:
                self._driver = driver_class(self.driver_path)
            else:
                self._driver = driver_class()

        return self._driver

    def process_response(self, request, response, spider):
        if not self.enabled:
            return response

        need_load_js = bool(int(request.meta.get('need_load_js', False)))
        if not need_load_js:
            return response

