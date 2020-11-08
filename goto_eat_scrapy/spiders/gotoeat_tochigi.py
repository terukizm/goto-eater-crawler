import scrapy


class GotoeatTochigiSpider(scrapy.Spider):
    name = 'gotoeat-tochigi'
    allowed_domains = ['gotoeat-tochigi.jp']
    start_urls = ['http://gotoeat-tochigi.jp/']

    def parse(self, response):
        pass
