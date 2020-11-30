import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class AichiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl aichi -O aichi.csv
    """
    name = 'aichi'
    allowed_domains = [ 'gotoeat-aichi-shop.jp' ]
    start_urls = ['https://www.gotoeat-aichi-shop.jp/shop/']

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//section[@class="lcl-sbs__main"]//ul[@class="lcl-shop"]/li[@class="lcl-shop__item"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//h2[@class="lcl-shop__name"]/text()').get().strip()

            # ジャンル名が未設定になっているものがいくつかあるのでlogging
            genre_name = article.xpath('.//ul[@class="lcl-shop-tag"]/li[@class="lcl-shop-tag__item lcl-shop-tag__item--cat"]/text()').get()
            if not genre_name:
                self.logzero_logger.warning('  ジャンル名未指定: {}'.format(item['shop_name']))
            item['genre_name'] = genre_name
            item['area_name'] = article.xpath('.//ul[@class="lcl-shop-tag"]/li[@class="lcl-shop-tag__item lcl-shop-tag__item--area"]/text()').get()

            place = article.xpath('.//p[@class="lcl-shop__address"]/text()').get().strip()
            m = re.match(r'〒\s*(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address').strip()
            item['zip_code'] = m.group('zip_code').strip()
            item['tel'] = article.xpath('.//a[@class="lcl-shop__link lcl-shop__link--tel"]/@href').get()
            item['offical_page'] = article.xpath('.//a[@class="lcl-shop__link lcl-shop__link--web"]/@href').get()

            self.logzero_logger.debug(item)
            yield item

        # 「次へ」がなければ終了
        next_page = response.xpath('//nav[@class="pagination"]//a[@class="pagination-btn pagination-btn--next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
