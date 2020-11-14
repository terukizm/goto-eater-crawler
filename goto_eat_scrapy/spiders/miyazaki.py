import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class MiyazakiSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl miyazaki -O output.csv
    """
    name = 'miyazaki'
    allowed_domains = [ 'premium-gift.jp' ]

    start_urls = ['https://premium-gift.jp/gotoeatmiyazaki/use_store']

    def parse(self, response):
        # 各加盟店情報を抽出
        for card in response.xpath('//section[@class="l-store-section"]//div[@class="store-card__item"]'):
            item = ShopItem()
            # 店舗名、ジャンル名
            text = card.xpath('.//h3[@class="store-card__title"]/text()').get().strip()
            item['shop_name'], item['genre_name'] = self._ジャンル抽出(text)

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
        next_page = 'https://premium-gift.jp/gotoeatmiyazaki/use_store?events=page&id={}&store=&addr=&industry='.format(m.group('page'))
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

    def _ジャンル抽出(self, text: str):
        # 宮崎は"／"区切りで店舗名部分にジャンル名を無理やり入れているため、その書式であればジャンル名として利用する
        m = re.match(r'(?P<shop_name>.*)／(?P<genre_name>.*)', text)
        if m:
            shop_name = m.group('shop_name')
            # ただしジャンル名は記入ブレがあるため、それらを寄せる
            genre_name = m.group('genre_name')
            if genre_name in ['麵類', '麺類']:
                genre_name = '麺類'
            if genre_name in ['カフェ', 'カフェ・喫茶', 'カフェ・喫茶店']:
                genre_name = 'カフェ・喫茶店'
            if genre_name in ['アジア・エスニック', 'アジアン・エスニック']:
                genre_name = ['アジア・エスニック']
            return shop_name, genre_name

        # ジャンル名がなければ"飲食店"に寄せる
        return text, '飲食店'

