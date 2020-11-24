import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class shimaneSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl shimane -O 32_shimane.csv
    """
    name = 'shimane'
    allowed_domains = [ 'gotoeat-shimane.jp' ]

    start_urls = ['https://www.gotoeat-shimane.jp/inshokuten/']

    def parse(self, response):
        # 詳細ページから各加盟店情報を抽出
        for article in response.xpath('//div[@id="main"]//div[@class="com-location"]/ul/li'):
            url = article.xpath('.//a/@href').get()
            yield scrapy.Request(response.urljoin(url), callback=self.detail)

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@class="pagination"]/span[@class="next"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

    def detail(self, response):
        item = ShopItem()
        item['shop_name'] = response.xpath('//h1[@class="title"]/text()').get().strip()
        item['address'] = response.xpath('//div[@class="info line addr"]/p/text()').get().strip()
        item['offical_page'] = response.xpath('//div[@class="info line url"]/p/text()').get()

        genre_name = response.xpath('//div[@class="info select genre"]/p/span/text()').get().strip()
        item['genre_name'] = ''.join(genre_name.split())

        tel = response.xpath('//div[@class="info line tel"]/p/text()').get()
        item['tel'] = tel.strip() if tel else None

        yield item
