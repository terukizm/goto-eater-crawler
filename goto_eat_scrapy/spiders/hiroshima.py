import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class HiroshimaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl hiroshima -O 34_hiroshima.csv
    """
    name = 'hiroshima'
    allowed_domains = [ 'gotoeat.hiroshima.jp' ]

    start_urls = ['https://gotoeat.hiroshima.jp/?s']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@class="result"]/div[@class="result__row"]'):
            item = ShopItem()
            item['genre_name'] = article.xpath('.//ul[@class="result__cate"]/li/text()').get().strip()
            item['shop_name'] = ''.join(article.xpath('.//div[@class="result__data"]/h3/a/text() | .//div[@class="result__data"]/h3/text()').getall()).strip()

            item['offical_page'] = article.xpath('.//div[@class="result__data"]/h3/a/@href').get()
            item['address'] = article.xpath('.//div[@class="result__data"]/p[@class="result__address"]/text()').get().strip()

            yield item

        # 「»」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
