import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class KyotoSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl kyoto -O output.csv
    """
    name = 'kyoto'
    allowed_domains = [ 'kyoto-gotoeat.com' ]   # .com とは

    # 全ジャンルを手動選択
    genre_list = [
        "居酒屋",
        "ラーメン・つけ麺",
        "中華料理",
        "和食",
        "郷土料理",
        "アジア・エスニック料理",
        "寿司・魚料理",
        "洋食・西洋料理",
        "カフェ・スイーツ",
        "うどん・そば",
        "カレー",
        "ホテルレストラン",
        "鍋",
        "焼肉・ホルモン",
        "その他",
        "お好み焼き・たこ焼き",
        "イタリアン・フレンチ",
    ]
    start_urls = [
        'https://kyoto-gotoeat.com/?area=&category_name={}'.format(','.join(genre_list))
    ]

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//main[@id="main"]//div[@class="store-item"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[@class="name"]/a/text()').get().strip()
            # テーブル部分
            table = article.xpath('.//table')
            # 「ジャンル」
            item['genre_name'] = table.xpath('.//tr[1]/td/text()').get().strip()
            # 「住所」
            item['address'] = table.xpath('.//tr[3]/td/text()').get().strip()
            # 「電話番号」
            item['tel'] = table.xpath('.//tr[4]/td/text()').get()
            # 「U R L」
            item['offical_page'] = table.xpath('.//tr[5]/td/text()').get()

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
