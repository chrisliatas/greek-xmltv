# -*- coding: utf-8 -*-
import scrapy
from scrapy_splash import SplashRequest
from datetime import datetime, timedelta

from ..items import XmltvItem, Programme
from . import DIGEA_EPG_GR

START_URL = DIGEA_EPG_GR


class DigeaSpider(scrapy.Spider):
    name = 'digea'
    allowed_domains = ['digea.gr']
    start_urls = [START_URL]
    custom_settings = {"FEED_FORMAT": "json", "FEED_URI": "export/digea_%(time)s.json"}
    today = datetime.today()

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 5})

    def parse(self, response):
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
            channel = XmltvItem()
            # returns channels ids, from html id.
            channel["id"] = chanl.xpath('@id').get()
            # returns: ALPHA, ANT1, OPEN BEYOND,...
            channel["name"] = chanl.xpath('@*[name()="tv:channel"]').get()
            # image urls
            channel["img_url"] = nat_chanl_imgs[i]
            channel["programmes"] = []
            dt_prevT = datetime.strptime('06.00', '%H.%M').time()
            for prg in chanl:
                p = Programme()
                p["desc"] = prg.xpath('./div/div/text()').get().strip()
                newT = prg.xpath('./li/p[@class="time"]/text()').get()
                p["start"] = newT
                dt_newT = datetime.strptime(newT, '%H.%M').time()
                if dt_newT > dt_prevT:
                    p["date"] = datetime.today().strftime('%Y%m%d')
                else:
                    p["date"] = (datetime.today() + timedelta(days=1)).strftime('%Y%m%d')
                dt_prevT = dt_newT
                p["title"] = prg.xpath('./li/p[3]/a/text()').get()
                channel["programmes"].append(p)
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
