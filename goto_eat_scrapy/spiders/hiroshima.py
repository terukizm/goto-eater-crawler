import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class HiroshimaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl hiroshima -O hiroshima.csv
    """
    name = 'hiroshima'
    allowed_domains = [ 'gotoeat.hiroshima.jp' ]
    start_urls = ['https://gotoeat.hiroshima.jp/?s']

    def parse(self, response):
        # 各加盟店情報を抽出
        # MEMO: 広島のエリア情報は検索条件指定以外で取得する方法がない
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@class="result"]/div[@class="result__row"]'):
            item = ShopItem()
            item['genre_name'] = article.xpath('.//ul[@class="result__cate"]/li/text()').get().strip()

            text = article.xpath('.//div[@class="result__data"]/h3/a/text() | .//div[@class="result__data"]/h3/text()').getall()
            item['shop_name'] = ''.join(text).strip()

            item['official_page'] = article.xpath('.//div[@class="result__data"]/h3/a/@href').get()
            item['address'] = article.xpath('.//div[@class="result__data"]/p[@class="result__address"]/text()').get().strip()


            yield item

        # 「»」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
