__author__ = 'socoboy'
import scrapy


class FreeProxyListSpider(scrapy.Spider):
    name = 'freeproxylist'
    allowed_domains = ['http://www.freeproxylists.net']
    start_urls = ['http://www.freeproxylists.net']

    def parse(self, response):
        filename = response.url.split("/")[-2]
        with open(filename, 'wb') as f:
            f.write(response.body)