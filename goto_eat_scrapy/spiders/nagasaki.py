import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class NagasakiSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl nagasaki -O 42_nagasaki.csv
    """
    name = 'nagasaki'
    allowed_domains = [ 'gotoeat-nagasaki.jp' ]

    start_urls = ['https://www.gotoeat-nagasaki.jp/merchant-list/']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//section[@id="shop-list"]/div[@class="shop-list-content"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[@class="shop-list-content-name"]/text()').get().strip()

            # 「ジャンル」
            text = ''.join(article.xpath('.//div[@class="shop-list-content-cat"]/text()').getall())
            item['genre_name'] = text.strip()

            item['address'] = article.xpath('.//div[@class="shop-list-content-add-002"]/text()').get().strip()
            item['tel'] = article.xpath('.//div[@class="shop-list-content-tel-002"]/text()').get()
            item['offical_page'] = article.xpath('.//div[@class="shop-list-content-url"]/a/@href').get()

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@class="pagination"]/a[@class="next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
