# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from enum import Enum


class ProxiesItem(scrapy.Item):
    # define the fields for your item here like:
    ip = scrapy.Field()
    port = scrapy.Field()
    protocol = scrapy.Field()
    anonymity = scrapy.Field()
    country = scrapy.Field()
    region = scrapy.Field()
    uptime = scrapy.Field()
    response = scrapy.Field()
    transfer = scrapy.Field()


class Fields(Enum):
    ip = 'ip'
    port = 'port'
    protocol = 'protocol'
    anonymity = 'anonymity'
    country = 'country'
    region = 'region'
    uptime = 'uptime'
    response = 'response'
    transfer = 'transfer'
