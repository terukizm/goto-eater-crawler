import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class NaraSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl nara -O nara.csv
    """
    name = 'nara'
    allowed_domains = [ 'premium-gift.jp' ]
    start_urls = ['https://premium-gift.jp/nara-eat/use_store']

    def __init__(self, logfile=None, *args, **kwargs):
        super().__init__(logfile, *args, **kwargs)

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//section[@class="l-store-section"]//div[@class="store-card__item"]'):
            item = ShopItem()
            item['shop_name'] = ' '.join(article.xpath('.//h3[@class="store-card__title"]/text()').getall()).strip()
            item['genre_name'] = article.xpath('.//p[@class="store-card__tag"]/text()').get().strip()

            place = article.xpath('.//table/tbody/tr[1]/td/text()').get().strip()
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')

            tel = article.xpath('.//table/tbody/tr[2]/td/text()').get().strip()
            item['tel'] = '' if tel == '-' else tel

            offical_page = article.xpath('.//table/tbody/tr[3]/td/text()').get().strip()
            item['offical_page'] = None if offical_page == '-' else offical_page    # "-" 表記は公式ページなし

            self.logzero_logger.debug(item)
            yield item

        # 「次へ」がなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@class="pagenation"]/a[contains(text(),"次へ")]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        m = re.match(r"^javascript:on_events\('page',(?P<page>\d+)\);$", next_page)
        next_page = 'https://premium-gift.jp/nara-eat/use_store?events=page&id={}&store=&addr=&industry='.format(m.group('page'))
        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
