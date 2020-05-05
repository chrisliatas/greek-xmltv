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
# generate listings for all available Digea and Ert regions
jtoXtv.generate_xmltv()
# generate listings for National & Attica Digea and Ert regions
jtoXtv.xmltv_file = 'grxmltv_nat_el.xml'
jtoXtv.generate_xmltv(pref_regions=('Nationwide', 'Attica-R-Z-9', 'National-public'))
