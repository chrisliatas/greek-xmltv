# Crawl process for spider Digea

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from xmltv.spiders.digea import DigeaSpider


process = CrawlerProcess(get_project_settings())
process.crawl(DigeaSpider)
process.start()
