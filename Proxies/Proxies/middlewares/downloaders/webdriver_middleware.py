__author__ = 'socoboy'
from selenium import webdriver
import os


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
            if self.driver_name == 'phantomjs':
                driver_class = webdriver.PhantomJS
            elif self.driver_name == 'chrome':
                driver_class = webdriver.Chrome
            elif self.driver_name == 'firefox':
                driver_class = webdriver.Firefox
            else:
                driver_class = webdriver.Chrome

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

        current_dir = os.getcwd()
        html_path = current_dir + 'webpage.html'
        with open(html_path, 'w') as f:
            f.write(response.body)

        self.driver.get('file://' + html_path)
        with open(current_dir + 'webpage.loaded.html') as f:
            f.write(self.driver.page_source)

        return response