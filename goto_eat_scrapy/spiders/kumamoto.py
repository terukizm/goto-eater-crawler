import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class KumamotoSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl kumamoto -O 43_kumamoto.csv
    """
    name = 'kumamoto'
    allowed_domains = [ 'gotoeat-kumamoto.jp' ]

    start_urls = ['https://gotoeat-kumamoto.jp/shop']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//section[@id="sale-page"]//div[@class="sec-body__inner"]/article'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//h3/text()').get().strip()

            place = article.xpath('.//p[1]/text()').get().strip()
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')

            item['offical_page'] = article.xpath('.//p[3]/a/@href').get()

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@class="pagination"]/a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
