# -*- coding: utf-8 -*-
import scrapy
from scrapy_splash import SplashRequest

from ..items import XmltvItem
from . import DIGEA_EPG_GR

START_URL = DIGEA_EPG_GR


class DigeaSpider(scrapy.Spider):
    name = 'digea'
    allowed_domains = ['digea.gr']
    start_urls = [START_URL]
    custom_settings = {"FEED_FORMAT": "jsonlines", "FEED_URI": "export/digea_%(time)s.jsonl"}

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 5})

    def parse(self, response):
        channel = XmltvItem()
        National_section = response.xpath('//*[@id="Nationwide"]')
        National_channels_imgs = National_section.xpath('./div[1]/div/div/div[1]/ul/*')
        National_channels = National_section.xpath('./div[1]/div/div/div[2]/ul[contains(@id,"channel-")]')

        print(F"Images for National channels found: {len(National_channels_imgs)}")
        print(f"National channels found: {len(National_channels)}")
        # Get National channel images
        nat_chanl_imgs = [
            response.urljoin(i)
            for i in National_channels_imgs.xpath('./a/img/@src').get()
        ]
        # National channels:
        # Fields: id, tv:channel,
        for i, chanl in enumerate(National_channels):
            # returns channels ids, from html id.
            channel["id"] = chanl.xpath('@id').get()
            # returns: ALPHA, ANT1, OPEN BEYOND,...
            channel["name"] = chanl.xpath('@*[name()="tv:channel"]').get()
            # image urls
            channel["img_url"] = nat_chanl_imgs[i]
            # //*[@id="epgpop"]
            # //*[@id="popupCalled10007450613"]
            # //*[@id="channel-100"]/li[1]
            yield channel

        # Regional_section = response.xpath('//*[@id="Regional"]')
        # Regional_subsections = Regional_section.xpath('//*[@id="myTabContentInside"]/div[contains(@class,"tab-pane")]')

        # for section in pages.xpath('./ul[@id="epgTabInside"]'):
        #     for channels in section.xpath('./ul[@id="epgTabInside"]'):
        #         next_page = channels.css("h4 a::attr(href)").get()
                # yield response.follow(next_page, callback=self.parse_channels)

    def parse_channels(self, response):
        print('parsing channels...')
        # main_img = response.xpath(
        #     '//*[contains(@id,"article-")]/div[1]/meta/@content'
        # ).get()
        # art_imgs = [
        #     response.urljoin(i)
        #     for i in response.xpath(
        #         '//*[contains(@id,"article-")]/div[@property="text"]//descendant::img/@src'
        #     ).getall()
        # ]
        # if main_img:
        #     art_imgs.append(main_img)
        # # print('The image contents are: ', art_imgs)
        # yield {
        #     "art_ts": response.xpath('//*[contains(@id,"article-")]//time/@datetime').get(),
        #     "art_url": response.xpath('/html/head/link/@href').get(),
        #     "art_title": response.xpath('/html/head/title/text()').get(),
        #     "file_urls": art_imgs,
        # }
