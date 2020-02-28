# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest
from datetime import datetime, timedelta

from ..items import XmltvItem

START_URL = 'https://www.digea.gr/EPG/el'


class DigeaSpider(scrapy.Spider):
    name = 'digea'
    allowed_domains = ['digea.gr']
    start_urls = [START_URL]
    custom_settings = {"FEED_FORMAT": 'json',
                       "FEED_URI": 'export/digea_%(time)s.json',
                       "FEED_EXPORT_ENCODING": 'utf-8',
                       "USER_AGENT": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/80.0.3987.106 Safari/537.36'
                       }

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 0.5})

    def parse(self, response):
        National_section = response.xpath('//*[@id="Nationwide"]')
        National_channels_imgs = National_section.xpath('./div[1]/div/div/div[1]/ul/*')
        National_channels = National_section.xpath('./div[1]/div/div/div[2]/ul[contains(@id,"channel-")]')

        print(F"Images for National channels found: {len(National_channels_imgs)}")
        print(f"National channels found: {len(National_channels)}")
        # Get National channel images
        nat_chanl_imgs = [
            response.urljoin(i.xpath('./a/img/@src').get())
            for i in National_channels_imgs
        ]
        # National channels:
        for i, chanl in enumerate(National_channels):
            l = ItemLoader(item=XmltvItem(), selector=chanl)
            # returns channels ids, from html id.
            l.add_xpath('id', '@id')
            # returns: ALPHA, ANT1, OPEN BEYOND,...
            l.add_xpath('name', '@*[name()="tv:channel"]')
            # image urls
            l.add_value('img_url', nat_chanl_imgs[i])
            tprg = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 6, 0, 0)
            progsx = chanl.xpath('./*')
            for prg_div, prg_li in zip(progsx[::2], progsx[1::2]):
                newt = prg_li.xpath('./p[@class="time"]/text()').get()
                h = int(newt[:2])
                m = int(newt[-2:])
                if tprg.time() <= datetime.strptime(newt, '%H:%M').time():
                    tprg = tprg + timedelta(hours=(h - tprg.hour), minutes=(m - tprg.minute))
                else:
                    tprg = tprg + timedelta(days=1, hours=(h - tprg.hour), minutes=(m - tprg.minute))
                p = {
                    "desc": prg_div.xpath('./div/text()').get().strip(),
                    "start": newt,
                    "date": tprg.strftime('%Y%m%d'),
                    "title": prg_li.xpath('./p[3]/a/text()').get()
                }
                l.add_value('programmes', p)
            yield l.load_item()

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
