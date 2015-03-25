__author__ = 'socoboy'
from scrapy import Spider, Request
from Proxies.items import ProxiesItem, Fields


class FreeProxyListSpider(Spider):
    name = 'freeproxylist'
    allowed_domains = ['http://www.freeproxylists.net']
    start_urls = ['http://www.freeproxylists.net']

    def make_requests_from_url(self, url):
        return Request(url, dont_filter=True, meta={'selenium_needed': True,
                                                    'page_handler': self.page_handler})

    def page_handler(self, driver, request):
        driver.get(request.url)
        return driver, request

    def parse(self, response):
        field_map_with_column = {
            u'IP Address': Fields.ip,
            u'Port': Fields.port,
            u'Protocol': Fields.protocol,
            u'Anonymity': Fields.anonymity,
            u'Country': Fields.country,
            u'Region': Fields.region,
            u'Uptime': Fields.uptime,
            u'Response': Fields.response,
            u'Transfer': Fields.transfer
        }

        column_map = {}
        for idx, sel in enumerate(response.css('table.DataGrid tr.Caption td')):
            column_name = sel.xpath('a/text()').extract()[0]
            if column_name in field_map_with_column:
                column_map[field_map_with_column[column_name]] = idx

        for sel in response.css('table.DataGrid tr:not(.Caption)'):
            item = ProxiesItem()
            sel_td = sel.css('td:not([colspan="10"])')
            if not sel_td:
                continue

            if Fields.ip in column_map:
                item[Fields.ip.name] = sel_td[column_map[Fields.ip]].xpath('a/text()').extract()

            if Fields.port in column_map:
                item[Fields.port.name] = sel_td[column_map[Fields.port]].xpath('text()').extract()

            if Fields.protocol in column_map:
                item[Fields.protocol.name] = sel_td[column_map[Fields.protocol]].xpath('text()').extract()

            if Fields.anonymity in column_map:
                item[Fields.anonymity.name] = sel_td[column_map[Fields.anonymity]].xpath('text()').extract()

            if Fields.country in column_map:
                item[Fields.country.name] = sel_td[column_map[Fields.country]].xpath('text()').extract()

            if Fields.region in column_map:
                item[Fields.region.name] = sel_td[column_map[Fields.region]].xpath('text()').extract()

            if Fields.uptime in column_map:
                item[Fields.uptime.name] = sel_td[column_map[Fields.uptime]].xpath('text()').extract()

            if Fields.response in column_map:
                item[Fields.response.name] = sel_td[column_map[Fields.response]].xpath('.//span/@style').extract()

            if Fields.transfer in column_map:
                item[Fields.transfer.name] = sel_td[column_map[Fields.transfer]].xpath('.//span/@style').extract()

            yield item