# Crawl process for spider Digea
# https://stackoverflow.com/questions/39365131/running-multiple-spiders-in-scrapy-for-1-website-in-parallel

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from xmltv.postproc import JsonToXmltv
from xmltv.spiders.digea import DigeaSpider
from xmltv.spiders.ertprog import ErtprogSpider

process = CrawlerProcess(get_project_settings())
process.crawl(DigeaSpider)
process.crawl(ErtprogSpider)
process.start()
# process will block here until both spiders have finished.
# Merge the json files produced:
jtoXtv = JsonToXmltv(multi_json=True)
jtoXtv.generate_xmltv()
# jtoXtv_all = JsonToXmltv(xmltv_file='grxmltv_el.xml', multi_json=True)
# jtoXtv_all.generate_xmltv()
