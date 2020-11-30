import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class AomoriSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl aomori -O aomori.csv
    """
    name = 'aomori'
    allowed_domains = [ 'premium-gift.jp' ]
    start_urls = ['https://premium-gift.jp/aomori/use_store']

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//section[@class="l-store-section"]//div[@class="store-card__item"]'):
            item = ShopItem()
            item['shop_name'] = ' '.join(article.xpath('.//h3[@class="store-card__title"]/text()').getall()).strip()
            item['genre_name'] = article.xpath('.//p[@class="store-card__tag"]/text()').get().strip()

            place = article.xpath('.//table/tbody/tr/th[contains(text(), "住所：")]/following-sibling::td/text()').get().strip()
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')

            tel = article.xpath('.//table/tbody/tr/th[contains(text(), "電話番号：")]/following-sibling::td/text()').get().strip()
            item['tel'] = '' if tel == '-' else tel

            item['official_page'] = article.xpath('.//table/tbody/tr/th[contains(text(), "URL：")]/following-sibling::td/a/@href').get()
            item['detail_page'] = article.xpath('.//a[@class="store-card__button"]/@href').get()

            self.logzero_logger.debug(item)
            yield item

        # 「次へ」がなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@class="pagenation"]/a[contains(text(),"次へ")]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        m = re.match(r"^javascript:on_events\('page',(?P<page>\d+)\);$", next_page)
        next_page = 'https://premium-gift.jp/aomori/use_store?events=page&id={}&store=&addr=&industry='.format(m.group('page'))
        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
