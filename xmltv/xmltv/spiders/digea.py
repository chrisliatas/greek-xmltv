# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Iterable
from urllib.parse import urljoin

import scrapy
from pytz import timezone
from scrapy.loader import ItemLoader

from ..items import XmltvItem

LOCAL_TZ = 'Europe/Athens'
DEFAULT_PRG_DECR_EL = 'Δεν υπάρχουν πληροφορίες προγράμματος'
BASE_URL = 'https://www.digea.gr'
API_PREFIX = '/el/api/epg'

REGION_SLUGS: dict[str, str] = {
    'ee': 'Nationwide',
    'pz1': 'E-Macedonia-Thrace-R-Z-1',
    'pz2_3': 'C-Macedonia-R-Z-2-3',
    'pz4': 'W-Macedonia-R-Z-4',
    'pz5': 'W-Greece-R-Z-5',
    'pz6': 'Peloponnese-R-Z-6',
    'pz7': 'Thessaly-R-Z-7',
    'pz8': 'C-Greece-R-Z-8',
    'pz9': 'Attica-R-Z-9',
    'pz10': 'Crete-R-Z-10',
    'pz11': 'Dodecanese-Samos-R-Z-11',
    'pz12': 'Cyclades-R-Z-12',
    'pz13': 'NE-Aegean-R-Z-13',
}


class DigeaSpider(scrapy.Spider):
    name = 'digea'
    allowed_domains = ['www.digea.gr', 'digea.gr']
    custom_settings = {
        "FEED_FORMAT": 'json',
        "FEED_URI": 'export/digea_%(time)s.json',
        "FEED_EXPORT_ENCODING": 'utf-8',
        "USER_AGENT": (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
    }

    def start_requests(self) -> Iterable[scrapy.Request]:
        # The new Digea site exposes JSON endpoints for regions, channels,
        # and programme events. Begin by retrieving the region metadata so we
        # can map API identifiers to the legacy region names used elsewhere
        # in the project.
        regions_url = urljoin(BASE_URL, f'{API_PREFIX}/get-perioxes')
        yield scrapy.Request(regions_url, callback=self.parse_regions)

    def parse_regions(
        self, response: scrapy.http.Response
    ) -> Iterable[scrapy.Request]:
        regions: list[dict[str, str]] = response.json()
        region_lookup = {
            reg['id']: REGION_SLUGS.get(reg['id'], reg['id']) for reg in regions
        }

        channels_url = urljoin(BASE_URL, f'{API_PREFIX}/get-channels')
        yield scrapy.Request(
            channels_url,
            callback=self.parse_channels,
            cb_kwargs={'region_lookup': region_lookup},
        )

    def parse_channels(
        self, response: scrapy.http.Response, region_lookup: dict[str, str]
    ) -> Iterable[scrapy.Request]:
        channels = response.json()
        # Keep the raw channel definitions handy when parsing programme events.
        events_date = date.today().isoformat()
        events_url = urljoin(BASE_URL, f'{API_PREFIX}/get-events?date={events_date}')
        yield scrapy.Request(
            events_url,
            callback=self.parse_events,
            cb_kwargs={'channels': channels, 'region_lookup': region_lookup},
        )

    def parse_events(
        self,
        response: scrapy.http.Response,
        channels: list[dict[str, str]],
        region_lookup: dict[str, str],
    ) -> Iterable[XmltvItem]:
        events: list[dict[str, str]] = response.json()
        events_by_channel: dict[str, list[dict[str, str]]] = {}

        # Group events by channel id to simplify programme construction.
        for event in events:
            channel_id = str(event.get('channel_id', '')).strip()
            if not channel_id:
                continue
            events_by_channel.setdefault(channel_id, []).append(event)

        for channel in channels:
            channel_id = str(channel.get('id', '')).strip()
            if not channel_id:
                continue

            programmes = self._parse_programmes(
                events_by_channel.get(channel_id, [])
            )

            loader = ItemLoader(item=XmltvItem())
            loader.add_value('id', f'channel-{channel_id}')
            loader.add_value('region', self._get_region(channel, region_lookup))
            loader.add_value('name', channel.get('name', '').strip())
            loader.add_value('img_url', urljoin(BASE_URL, channel.get('img', '')))
            loader.add_value('programmes', programmes)
            yield loader.load_item()

    @staticmethod
    def _get_region(channel: dict[str, str], lookup: dict[str, str]) -> str:
        """Map API region ids to legacy region names for downstream consumers."""
        return lookup.get(channel.get('regional_zone_id', ''), 'Unknown')

    def _parse_programmes(self, events: list[dict[str, str]]) -> list[dict[str, str]]:
        programmes: list[dict[str, str]] = []
        local_tz = timezone(LOCAL_TZ)

        for event in sorted(events, key=lambda ev: ev.get('actual_time', '')):
            start_raw = event.get('actual_time')
            end_raw = event.get('end_time')
            title = event.get('title', '').strip() or DEFAULT_PRG_DECR_EL
            description = (
                event.get('long_synopsis')
                or event.get('synopsis')
                or DEFAULT_PRG_DECR_EL
            )

            if not start_raw:
                continue

            # Events are returned as naive timestamps in local time; attach
            # the Athens timezone so downstream processing receives consistent
            # data. If the API ever returns tz-aware timestamps, normalize
            # them to Athens instead of re-localizing.
            start_dt_raw = datetime.fromisoformat(start_raw)
            if start_dt_raw.tzinfo is None:
                start_dt = local_tz.localize(start_dt_raw)
            else:
                start_dt = start_dt_raw.astimezone(local_tz)

            end_dt = start_dt
            if end_raw:
                end_dt_raw = datetime.fromisoformat(end_raw)
                if end_dt_raw.tzinfo is None:
                    end_dt = local_tz.localize(end_dt_raw)
                else:
                    end_dt = end_dt_raw.astimezone(local_tz)

            programmes.append(
                {
                    "desc": description,
                    "start": start_dt.strftime('%H:%M'),
                    "date": start_dt.strftime('%Y%m%d'),
                    "airDateTime": start_dt.strftime('%Y%m%d%H%M%S %z'),
                    "title": title,
                    "end": end_dt.strftime('%Y%m%d%H%M%S %z'),
                }
            )

        return programmes
