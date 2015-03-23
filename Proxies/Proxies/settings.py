# -*- coding: utf-8 -*-

# Scrapy settings for Proxies project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'Proxies'

SPIDER_MODULES = ['Proxies.spiders']
NEWSPIDER_MODULE = 'Proxies.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'Proxies (+http://www.yourdomain.com)'

# DOWNLOADER_MIDDLEWARES = {
#     'Proxies.middlewares.downloaders.WebDriverDownloaderMiddleware': 543,
# }

DOWNLOAD_HANDLERS = {
    'http': 'Proxies.download_handlers.SeleniumDownloadHandler',
    'https': 'Proxies.download_handlers.SeleniumDownloadHandler'
}

# Setting for using selenium webdriver for load javascript
# WEB_DRIVER_ENABLED => enable web driver
WEB_DRIVER_ENABLED = True
# WEB_DRIVER_NAME availables: phantomjs, chrome, firefox, opera, ie, Default: phantomjs
WEB_DRIVER_NAME = 'chrome'
# WEB_DRIVER_PATH: path to webdriver executable