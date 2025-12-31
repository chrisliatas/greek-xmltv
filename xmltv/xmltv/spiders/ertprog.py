# -*- coding: utf-8 -*-
from datetime import datetime
from itertools import count
from urllib.parse import urljoin

import scrapy
from pytz import timezone
from scrapy.loader import ItemLoader

from ..items import XmltvItem

START_URL = 'https://www.ert.gr/tv/program/'
ERT_CHANNELS = [
    'ert1',
    'ert2',
    'ert3',
    'ertnews',
    'ertsports',
    'vouli',
]
LOCAL_TZ = 'Europe/Athens'
DEFAULT_PRG_DECR_EL = 'Δεν υπάρχουν πληροφορίες προγράμματος'
# Counter to create channel id numbers similar to digea ones.
chnl_cntr = count(start=10, step=10)


class ErtprogSpider(scrapy.Spider):
    name = 'ertprog'
    allowed_domains = ['www.ert.gr', 'ert.gr']
    start_urls = [urljoin(START_URL, f'{slug}/') for slug in ERT_CHANNELS]
    custom_settings = {
        "FEED_FORMAT": 'json',
        "FEED_URI": 'export/ert_%(time)s.json',
        "FEED_EXPORT_ENCODING": 'utf-8',
        "USER_AGENT": (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
    }

    def parse(self, response):
        if response.status != 200:
            self.logger.warning(
                "ERT program page returned status %s for %s",
                response.status,
                response.url,
            )
            return

        channel_logo = response.xpath(
            "//div[contains(@class,'broadcast')]//img[contains(@src,'logo')][1]/@src"
        ).get()
        channel_name = response.xpath(
            "//div[contains(@class,'broadcast')]//img[contains(@src,'logo')][1]/@alt"
        ).get()
        if not channel_name:
            channel_name = response.url.rstrip('/').split('/')[-1].upper()

        articles = response.xpath("//article[@data-start-time]")
        programmes = []
        for article in articles:
            programme = self._parse_programme(article)
            if programme:
                programmes.append(programme)

        if not programmes:
            self.logger.warning("No programme entries parsed for %s.", response.url)

        loader = ItemLoader(item=XmltvItem(), response=response)
        loader.add_value('id', f'channel-0{str(next(chnl_cntr))}')
        loader.add_value('region', 'National-public')
        loader.add_value('name', channel_name.strip())
        loader.add_value('img_url', response.urljoin(channel_logo or ''))
        loader.add_value('programmes', programmes)
        yield loader.load_item()

    @staticmethod
    def _parse_programme(article) -> dict | None:
        start_raw = article.attrib.get("data-start-time")
        end_raw = article.attrib.get("data-end-time")
        if not start_raw:
            return None

        start_dt = ErtprogSpider._parse_datetime(start_raw)
        end_dt = ErtprogSpider._parse_datetime(end_raw) if end_raw else start_dt

        title = article.xpath(
            ".//strong[contains(@class,'section-title')]/text()"
        ).get(default="").strip()
        desc_parts = article.xpath(
            ".//*[self::em or self::span][contains(@class,'fs-ms')]/text()"
        ).getall()
        desc = " ".join(
            part.strip().replace("\xa0", " ") for part in desc_parts if part.strip()
        ).strip()

        return {
            "desc": desc or DEFAULT_PRG_DECR_EL,
            "start": start_dt.strftime('%H:%M'),
            "date": start_dt.strftime('%Y%m%d'),
            "airDateTime": start_dt.strftime('%Y%m%d%H%M%S %z'),
            "title": title or DEFAULT_PRG_DECR_EL,
            "end": end_dt.strftime('%Y%m%d%H%M%S %z'),
        }

    @staticmethod
    def _parse_datetime(raw_value: str) -> datetime:
        local_tz = timezone(LOCAL_TZ)
        try:
            parsed = datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S%z")
        except ValueError:
            parsed = datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S")
        if parsed.tzinfo is None:
            return local_tz.localize(parsed)
        return parsed.astimezone(local_tz)
