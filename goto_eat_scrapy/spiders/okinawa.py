import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class OkinawaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl okinawa -O okinawa.csv
    """
    name = 'okinawa'
    allowed_domains = [ 'gotoeat.okinawa.jp' ]
    start_urls = ['https://gotoeat.okinawa.jp/restaurant/']

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@class="search_result"]//article'):
            item = ShopItem()
            item['area_name'] = article.xpath('.//p[@class="category"]/a[@class="areas"]/text()').get()
            item['genre_name'] = article.xpath('.//p[@class="category"]/a[@class="industry"]/text()').get()
            item['shop_name'] = article.xpath('.//h4[@class="title"]/text()').get().strip()

            address = article.xpath('.//p[@class="address"]/text()').get().strip()
            m = re.match(r'(?P<zip_code>[0-9]{3}-[0-9]{4}\s+?)*(?P<address>.*)', address.strip())
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')  # 郵便番号は入ってたり入ってなかったりが混在

            tel = article.xpath('.//div[@class="column"]/p[@class="tel"]/a/text()').get()
            item['tel'] = tel.replace('TEL:', '') if tel else None
            item['official_page'] = article.xpath('.//div[@class="column"]/p[@class="url"]/a[@rel="noopener"]/@href').get()

            self.logzero_logger.debug(item)
            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@role="navigation"]//li/span[@aria-current="page"]/../following-sibling::li/a/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
