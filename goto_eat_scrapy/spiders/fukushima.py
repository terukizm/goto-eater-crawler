import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class FukushimaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl fukushima -O 07_fukushima.csv
    """
    name = 'fukushima'
    allowed_domains = [ 'gotoeat-fukushima.jp' ]

    start_urls = ['https://gotoeat-fukushima.jp/shop/?s=']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@class="block_search-result"]/ul[@class="list_search-result"]/li'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//a/h3[@class="result-name"]/span/text()').get().strip()
            item['address'] = article.xpath('.//a/p[@class="result-address"]/span/text()').get().strip()
            item['genre_name'] = article.xpath('.//a/p[@class="result-cat"]/span/text()').get().strip()

            # 以下は詳細ページのPOPUP部分から取得
            item['tel'] = article.xpath('.//div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[3]/span[@class="info-text"]/text()').get()
            item['opening_hours'] = article.xpath('.//div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[4]/span[@class="info-text"]/text()').get()
            item['closing_day'] = article.xpath('.//div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[5]/span[@class="info-text"]/text()').get()
            item['offical_page'] = article.xpath('.//div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[6]/span[@class="info-text"]/a/@href').get()
            yield item

        # 「NEXT」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)