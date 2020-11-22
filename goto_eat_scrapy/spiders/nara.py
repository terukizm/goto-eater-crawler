import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class NaraSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl nara -O 29_nara.csv
    """
    name = 'nara'
    allowed_domains = [ 'premium-gift.jp' ]

    start_urls = ['https://premium-gift.jp/nara-eat/use_store']

    def parse(self, response):
        # 各加盟店情報を抽出
        for card in response.xpath('//section[@class="l-store-section"]//div[@class="store-card__item"]'):
            item = ShopItem()
            item['shop_name'] = ' '.join(card.xpath('.//h3[@class="store-card__title"]/text()').getall()).strip()
            item['genre_name'] = card.xpath('.//p[@class="store-card__tag"]/text()').get().strip()
            # テーブル部分
            table = card.xpath('.//table/tbody')
            # 「郵便番号」「住所」
            place = table.xpath('.//tr[1]/td/text()').get().strip()
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')
            # 「電話番号」
            tel = table.xpath('.//tr[2]/td/text()').get().strip()
            item['tel'] = '' if tel == '-' else tel
            # 「URL」
            offical_page = table.xpath('.//tr[3]/td/text()').get().strip()
            item['offical_page'] = '' if offical_page == '-' else offical_page

            yield item

        # 「次へ」がなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@class="pagenation"]/a[contains(text(),"次へ")]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        m = re.match(r"^javascript:on_events\('page',(?P<page>\d+)\);$", next_page)
        next_page = 'https://premium-gift.jp/nara-eat/use_store?events=page&id={}&store=&addr=&industry='.format(m.group('page'))
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
