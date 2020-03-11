# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class XmltvItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # pass
    id = scrapy.Field()
    region = scrapy.Field()
    name = scrapy.Field()
    img_url = scrapy.Field()
    programmes = scrapy.Field()


# class Programme(scrapy.Item):
#     start = scrapy.Field()
#     date = scrapy.Field()
#     title = scrapy.Field()
#     desc = scrapy.Field()
