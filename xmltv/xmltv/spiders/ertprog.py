# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from itertools import count
from urllib.parse import urljoin, quote

import scrapy
from pytz import timezone
from scrapy.loader import ItemLoader

from ..items import XmltvItem

START_URL = 'https://program.ert.gr/'
# START_URL = 'https://webtv.ert.gr/'
ert_channels = [
    'Ert1',
    'Ert2',
    'Ert3',
    'ErtSportsHD',
    'Vouli'
    # 'programma-ert1',
    # 'programma-ert2',
    # 'programma-ert3',
    # 'programma-ertsportshd',
]
LOCAL_TZ = 'Europe/Athens'
DEFAULT_PRG_DECR_EL = 'Δεν υπάρχουν πληροφορίες προγράμματος'
# Counter to create channel id numbers similar to digea ones.
chnl_cntr = count(start=10, step=10)


class ErtprogSpider(scrapy.Spider):
    name = 'ertprog'
    allowed_domains = ['program.ert.gr']
    start_urls = [f'{urljoin(START_URL, x)}/' for x in ert_channels]
    custom_settings = {"FEED_FORMAT": 'json',
                       "FEED_URI": 'export/ert_%(time)s.json',
                       "FEED_EXPORT_ENCODING": 'utf-8',
                       "USER_AGENT": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/80.0.3987.106 Safari/537.36'
                       }

    def parse(self, response):
        main_t = response.xpath('/html/body/table[2]/tr[4]/td/table/tr/td[3]/table[1]/*')
        night_t = response.xpath('/html/body/table[2]/tr[4]/td/table/tr/td[3]/table[2]/*')
        chanl_img = response.urljoin(quote(main_t[2].xpath('./td/table/tr/td[1]/a/img/@src').get()))
        # date_txt = main_t[2].xpath('./td/table/tr/td[2]/table/tr/td[2]/b/text()').get()[-10:]
        loader = ItemLoader(item=XmltvItem(), response=response)
        loader.add_value('id', f'channel-0{str(next(chnl_cntr))}')
        loader.add_value('region', 'National-public')
        loader.add_value('name', f'{response.url.split("/")[3]}')
        loader.add_value('img_url', chanl_img)
        # Ert programs comprise of two tables, one until nigh and another for nightly repetitions.
        loader.add_value('programmes', self.parse_programs([*main_t[5::2], *night_t[5::2]]))
        yield loader.load_item()

    def parse_programs(self, response):
        tprg = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 5, 30, 0)
        tprg = timezone(LOCAL_TZ).localize(tprg)
        for prg in response:
            newt = prg.xpath('./td/text()').get()
            h = int(newt[:2])
            m = int(newt[-2:])
            if tprg.time() <= datetime.strptime(newt, '%H:%M').time():
                tprg = tprg + timedelta(hours=(h - tprg.hour), minutes=(m - tprg.minute))
            else:
                tprg = tprg + timedelta(days=1, hours=(h - tprg.hour), minutes=(m - tprg.minute))
            try:
                pg = f"[{prg.xpath('./td[3]/img/@src').get().split('/')[3].split('.')[0]}]"
            except AttributeError:
                pg = '[K16]'
            title = prg.xpath('./td[4]/table/tr/td[2]/a/text()').get().strip().replace('\n', ' ').replace('\xa0', '')
            details = prg.xpath('./td[4]/table/tr[2]/td[2]/font/text()').get()
            details = details.strip().replace('\n', ' ').replace('\xa0', '') if details else ''
            prg_type = prg.xpath('./td[4]/table/tr/td[2]/img/@alt').get()
            prg_type = prg_type.strip().replace('\n', ' ').replace('\xa0', '') if prg_type else ''
            descritpion = prg_type or ''
            if descritpion and details:
                descritpion = f'{descritpion} {details}'
            elif details and not descritpion:
                descritpion = details
            yield {
                "desc": descritpion or DEFAULT_PRG_DECR_EL,
                "start": newt,
                "date": tprg.strftime('%Y%m%d'),
                "airDateTime": tprg.strftime('%Y%m%d%H%M%S %z'),
                "title": f'{pg} {title}'
            }
