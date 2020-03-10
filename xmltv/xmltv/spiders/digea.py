# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest
from datetime import datetime, timedelta
from urllib.parse import urljoin

from ..items import XmltvItem

START_URL = 'https://www.digea.gr/EPG/el'
prefered_areas = [
    'Nationwide',
    # 'E-Macedonia-Thrace-R-Z-1',
    # 'C-Macedonia-R-Z-2-3',
    # 'W-Macedonia-R-Z-4',
    # 'W-Greece-R-Z-5',
    # 'Peloponnese-R-Z-6',
    # 'Thessaly-R-Z-7',
    # 'C-Greece-R-Z-8',
    'Attica-R-Z-9',
    # 'Crete-R-Z-10',
    # 'Dodecanese-Samos-R-Z-11',
    # 'Cyclades-R-Z-12',
    # 'NE-Aegean-R-Z-13',
]


class DigeaSpider(scrapy.Spider):
    name = 'digea'
    allowed_domains = ['digea.gr']
    start_urls = [urljoin(START_URL, f'#!{x}') for x in prefered_areas]
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
        # Get coverage area name from response url to get the name of the section to parse:
        section = f'//*[@id="{response.url[29:]}"]'
        section_imgs = [response.urljoin(i.xpath('./a/img/@src').get())
                        for i in response.xpath(f'{section}/div[1]/div/div/div[1]/ul/*')]

        for i, chanl in enumerate(response.xpath(f'{section}/div[1]/div/div/div[2]/ul[contains(@id,"channel-")]')):
            loader = ItemLoader(item=XmltvItem(), selector=chanl)
            # returns channels ids, from html id.
            loader.add_xpath('id', '@id')
            # returns: ALPHA, ANT1, OPEN BEYOND,...
            loader.add_xpath('name', '@*[name()="tv:channel"]')
            # image urls
            loader.add_value('img_url', section_imgs[i])
            # parse each channel's programmes
            loader.add_value('programmes', self.parse_programs(chanl))
            yield loader.load_item()

    def parse_programs(self, response):
        tprg = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 6, 0, 0)
        progsx = response.xpath('./*')
        for prg_div, prg_li in zip(progsx[::2], progsx[1::2]):
            newt = prg_li.xpath('./p[@class="time"]/text()').get()
            h = int(newt[:2])
            m = int(newt[-2:])
            if tprg.time() <= datetime.strptime(newt, '%H:%M').time():
                tprg = tprg + timedelta(hours=(h - tprg.hour), minutes=(m - tprg.minute))
            else:
                tprg = tprg + timedelta(days=1, hours=(h - tprg.hour), minutes=(m - tprg.minute))
            yield {
                "desc": prg_div.xpath('./div/text()').get().strip(),
                "start": newt,
                "date": tprg.strftime('%Y%m%d'),
                "title": prg_li.xpath('./p[3]/a/text()').get()
            }
