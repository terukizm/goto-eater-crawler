
import scrapy
import pathlib
import pandas as pd
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class FukuokaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl fukuoka -O 40_fukuoka.csv
    """
    name = 'fukuoka'
    allowed_domains = [ 'gotoeat-fukuoka.jp' ]

    start_urls = [
        'https://gotoeat-fukuoka.jp/csv/fk_gotoeat_UTF-8.csv',
    ]

    genre_list = [
        '', # genre_list[1]="和食・寿司" 〜 genre_list[15]="その他"
        '和食・寿司',
        '洋食',
        '中華料理',
        'フレンチ・イタリアン',
        'ラーメン・餃子',
        '焼肉・ホルモン・韓国料理',
        'すき焼き・しゃぶしゃぶ',
        'アジア・エスニック・各国料理',
        'カフェ・スイーツ',
        'ファミリーレストラン・食堂',
        '居酒屋',
        'バー・ダイニングバー',
        'ファーストフード',
        'うどん・そば・丼',
        'その他',
    ]

    def parse(self, response):
        # MEMO: tempfile, io.stringIO等ではきちんと動作しなかったので実ファイルに書き込んでいる
        tmp_csv = f'/tmp/temp_{self.name}.csv'
        with open(tmp_csv, 'wb') as f:
            f.write(response.body)

        # ここは特にpandasでやる理由ない…
        df = pd.read_csv(tmp_csv, dtype={'13.店舗情報ジャンル': int}, \
            usecols=('11.店舗情報：店舗名', '13.店舗情報ジャンル', '14.店舗住所：郵便番号', \
                '16.店舗住所：市町村', '17.店舗住所：町域、番地', '18.店舗住所：建物名', \
                '19.店舗情報：電話番号', '20.店舗ホームページ') \
        ).fillna({'17.店舗住所：町域、番地': '', '18.店舗住所：建物名': '', '20.店舗ホームページ': ''})

        for _, row in df.iterrows():
            item = ShopItem()
            item['shop_name'] = row['11.店舗情報：店舗名']
            item['genre_name'] = self.genre_list[row['13.店舗情報ジャンル']]    # 1〜15をmapping
            item['address'] = '{}{}{}'.format(row['16.店舗住所：市町村'], row['17.店舗住所：町域、番地'], row['18.店舗住所：建物名'])
            item['tel'] = row['19.店舗情報：電話番号']
            item['offical_page'] = row['20.店舗ホームページ']
            yield item

        pathlib.Path(tmp_csv)
