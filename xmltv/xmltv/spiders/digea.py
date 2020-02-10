# -*- coding: utf-8 -*-
import scrapy

from . import DIGEA_BASE_URL

NATIONWIDE = '#!Nationwide'
START_URL = DIGEA_BASE_URL + NATIONWIDE


class DigeaSpider(scrapy.Spider):
    name = 'digea'
    allowed_domains = ['digea.gr']
    start_urls = [START_URL]
    custom_settings = {"FEED_FORMAT": "csv", "FEED_URI": "export/digea_%(time)s.csv"}

    def parse(self, response):
        # relpath = article.xpath('./div[1]/a/@href')
        article_selector = ".nspArt"
        pages = response.xpath('//*[@id="nsp-nsp-460"]/div/div[2]/div/div')
        # print("Pages found in page: ", len(pages))
        for p in pages:
            for article in p.css(article_selector):
                next_page = article.css("h4 a::attr(href)").get()
                # yield {
                #     "name": article.css("h4 a ::text").get(),
                #     "abspath": response.urljoin(next_page),
                # }
                yield response.follow(next_page, callback=self.parse_newspage)

    def parse_newspage(self, response):
        main_img = response.xpath(
            '//*[contains(@id,"article-")]/div[1]/meta/@content'
        ).get()
        art_imgs = [
            response.urljoin(i)
            for i in response.xpath(
                '//*[contains(@id,"article-")]/div[@property="text"]//descendant::img/@src'
            ).getall()
        ]
        if main_img:
            art_imgs.append(main_img)
        # print('The image contents are: ', art_imgs)
        yield {
            "art_ts": response.xpath('//*[contains(@id,"article-")]//time/@datetime').get(),
            "art_url": response.xpath('/html/head/link/@href').get(),
            "art_title": response.xpath('/html/head/title/text()').get(),
            "file_urls": art_imgs,
        }
