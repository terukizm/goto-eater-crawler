import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class ToyamaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl toyama -O 16_toyama.csv
    """
    name = 'toyama'
    allowed_domains = [ 'toyamagotoeat.jp' ]

    start_urls = ['https://www.toyamagotoeat.jp/shop/']
    page_no = 1

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//ul[@class="list"]/li[@class="item"]'):
            item = ShopItem()
            item['genre_name'] = article.xpath('.//div[@class="item_header"]/text()').get().strip()
            item['shop_name'] = article.xpath('.//div[@class="item_body"]/div[@class="item_body_name"]/text()').get().strip()

            table = article.xpath('.//div[@class="item_body"]/div[@class="item_body_table"]')
            item['address'] = article.xpath('.//div[@class="place"]/div[@class="rig"]/text()').get().strip()
            item['tel'] = article.xpath('.//div[@class="phone"]/div[@class="rig"]/text()').get()
            item['opening_hours'] = article.xpath('.//div[@class="work"]/div[@class="rig"]/text()').get()
            item['closing_day'] = article.xpath('.//div[@class="off_day"]/div[@class="rig"]/text()').get()

            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//ul[@class="pagination_list"]/li[@class="next_post_link"]/a[@rel="prev"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.page_no += 1
        next_page = f'https://www.toyamagotoeat.jp/shop/page/{self.page_no}?area=all&type=&search='
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
