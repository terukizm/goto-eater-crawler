
import scrapy
import w3lib
import pathlib
import pandas as pd
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class AkitaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl akita -O 05_akita.csv
    """
    name = 'akita'
    allowed_domains = [ 'gotoeat-akita.com' ]    # .comとは

    start_urls = [
        'https://gotoeat-akita.com/csv/list.csv',
    ]

    def parse(self, response):
        # MEMO: tempfile, io.stringIO等ではきちんと動作しなかったので実ファイルに書き込んでいる
        tmp_csv = f'/tmp/temp_{self.name}.csv'
        with open(tmp_csv, 'wb') as f:
            f.write(response.body)

        # ここは特にpandasでやる理由ない…
        df = pd.read_csv(tmp_csv, header=None, dtype={'13.店舗情報ジャンル': int}, \
            names=('店舗名', '市町村', '所在地', '電話番号', '公式ホームページ')
        )

        for _, row in df.iterrows():
            item = ShopItem()
            # CSV中に <!-- --> 形式で検索用(?)のふりがな/フリガナが入っているので削除
            item['shop_name'] = w3lib.html.remove_tags(row['店舗名']).strip()

            # 同じく検索用(?)の文字列が入っていることがあるが、こちらの入力値は利用する
            # (申請時に未入力だった項目を検索用に手動で埋めてる？)
            item['address'] = row['所在地'].replace('<!--', '').replace('-->', '').strip()

            item['tel'] = row['電話番号']
            item['genre_name'] = '飲食店'    # ジャンルなし
            item['offical_page'] = row['公式ホームページ']
            yield item

        pathlib.Path(tmp_csv)
