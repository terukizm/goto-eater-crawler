
import scrapy
import w3lib
import pathlib
import pandas as pd
from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class AkitaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl akita -O akita.csv
    """
    name = 'akita'
    allowed_domains = [ 'gotoeat-akita.com' ]    # .comとは
    start_urls = ['https://gotoeat-akita.com/csv/list.csv']

    def __init__(self, logfile=None, *args, **kwargs):
        super().__init__(logfile, *args, **kwargs)

    def parse(self, response):
        # MEMO: tempfile, io.stringIO等ではpd.read_csv()がきちんと動作しなかったので
        # scrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)に書き込んでいる
        cache_dir = pathlib.Path.cwd() / '.scrapy' / settings.HTTPCACHE_DIR / self.name
        tmp_csv = str(cache_dir / 'list.csv')
        with open(tmp_csv, 'wb') as f:
            f.write(response.body)
        self.logzero_logger.info(f'💾 saved csv: {response.request.url} > {tmp_csv}')

        df = pd.read_csv(tmp_csv, header=None, \
            names=('店舗名', '市町村', '所在地', '電話番号', '公式ホームページ')
        ).fillna({'公式ホームページ': ''})

        for _, row in df.iterrows():
            item = ShopItem()
            # CSV中に <!-- --> 形式で検索用(?)のふりがな/フリガナが入っているので削除
            item['shop_name'] = w3lib.html.remove_tags(row['店舗名']).strip()

            # 同じく検索用(?)の文字列が入っているものがあるが、こちらの入力値は利用する
            # (申請時に未入力だった項目を手作業で埋めてる？)
            item['address'] = row['所在地'].replace('<!--', '').replace('-->', '').strip()

            item['tel'] = row['電話番号']
            item['offical_page'] = row['公式ホームページ']
            item['genre_name'] = None    # 秋田にはジャンル情報なし

            self.logzero_logger.debug(item)
            yield item
