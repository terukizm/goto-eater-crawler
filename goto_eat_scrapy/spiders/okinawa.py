import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class OkinawaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl okinawa -O 47_okinawa.csv
    """
    name = 'okinawa'
    allowed_domains = [ 'gotoeat.okinawa.jp' ]

    start_urls = ['https://gotoeat.okinawa.jp/restaurant/']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@class="search_result"]//article'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//h4[@class="title"]/text()').get().strip()

            address = article.xpath('.//p[@class="address"]/text()').get()
            if not address:     # 「ヒルトン沖縄北谷リゾート」が空データで入ってるためskip
                continue
            m = re.match(r'(?P<zip_code>[0-9]{3}-[0-9]{4}\s+?)*(?P<address>.*)', address.strip())
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')

            item['genre_name'] = article.xpath('.//p[@class="category"]/a[@class="industry"]/text()').get()

            tel = article.xpath('.//div[@class="column"]/p[@class="tel"]/a/text()').get()
            item['tel'] = tel.replace('TEL:', '') if tel else None
            item['offical_page'] = article.xpath('.//div[@class="column"]/p[@class="url"]/a[@rel="noopener"]/@href').get()

            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@role="navigation"]//li/span[@aria-current="page"]/../following-sibling::li/a/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
