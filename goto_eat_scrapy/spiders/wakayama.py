import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class WakayamaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl wakayama -O 30_wakayama.csv
    """
    name = 'wakayama'
    allowed_domains = [ 'gotoeat-wakayama.com' ]    # .comとは

    start_urls = ['https://gotoeat-wakayama.com/search/']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//ul[@class="result_list"]/li'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[1]/h3[@class="shop_name"]/text()').get().strip()
            item['genre_name'] = article.xpath('.//div[1]/ul[@class="shop_tag flex"]/li[@class="shop_cat"]/text()').get().strip()

            place = article.xpath('.//div[2]/p[@class="shop_address"]/text()').get().strip()
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')

            item['tel'] = article.xpath('.//div[2]/div[@class="shop_info flex"]/p[@class="shop_tel"]/text()').get()
            item['offical_page'] = article.xpath('.//div[2]/div[@class="shop_info flex"]/p[@class="shop_web"]/a/@href').get()

            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//button[@class="active"]/../../following-sibling::li/form/@action').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
