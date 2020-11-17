import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class SagaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl saga -O 41_saga.csv
    """
    name = 'saga'
    allowed_domains = [ 'gotoeat-saga.jp' ]

    start_urls = ['https://gotoeat-saga.jp/consumer/shop.php?name=#search_result']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//main[@id="primary"]//div[@class="shop_info"]/div[@class="shop_detail"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[@class="ttl"]/text()').get().strip()
            item['genre_name'] = article.xpath('.//div[@class="genre"]/text()').get().strip()

            item['address'] = ''.join(article.xpath('.//dl[1]/dd/text()').getall()).strip()
            item['tel'] = article.xpath('.//dl[2]/dd/text()').get()
            item['opening_hours'] = article.xpath('.//dl[3]/dd/text()').get()
            item['closing_day'] = article.xpath('.//dl[4]/dd/text()').get()
            item['offical_page'] = article.xpath('.//dl[5]/dd/a[@rel="noopener noreferrer"]/@href').get()
            yield item

        # 「NEXT」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@class="pagination"]/ul/li[@class="next"]/a/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
