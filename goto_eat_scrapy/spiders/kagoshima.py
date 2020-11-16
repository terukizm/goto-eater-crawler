
import scrapy
import tabula
import pathlib
import pandas as pd
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class KagoshimaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl kagoshima -O 46_kagoshima.csv
    """
    name = 'kagoshima'
    allowed_domains = [ 'www.kagoshima-cci.or.jp' ]

    start_urls = [
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/0.pdf',     # 「鹿児島市全域」 25ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/10.pdf',    # 「薩摩川内市」  3ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/11.pdf',    # 「鹿屋市」　3ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/12.pdf',    # 「枕崎市」　1ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/13.pdf',    # 「阿久根市」　1ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/14.pdf',    # 「奄美市」　3ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/15.pdf',    # 「南さつま市」　2ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/16.pdf',    # 「出水市」　2ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/17.pdf',    # 「指宿市」　2ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/18.pdf',    # 「いちき串木野市」　1ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/19.pdf',    # 「霧島市」　3ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/20.pdf',    # 「姶良市」　2ページくらい
        'http://www.kagoshima-cci.or.jp/wp-content/uploads/2020/11/21.pdf',    # 「その他地域」　3ページくらい
    ]

    def parse(self, response):
        # TODO: 行数確認

        # MEMO: tabula-pyはtempfile, io.stringIO等ではきちんと動作しなかったので実ファイルに書き込んでいる
        tmp_pdf = f'/tmp/temp_{self.name}.pdf'
        tmp_csv = f'/tmp/temp_{self.name}.csv'
        with open(tmp_pdf, 'wb') as f:
            f.write(response.body)

        tabula.convert_into(tmp_pdf, tmp_csv, output_format="csv", pages='all', lattice=True)
        df = pd.read_csv(tmp_csv, header=1, names=('店舗名', '所在地'))
        df = df.dropna(subset=['店舗名'])[df['店舗名'] != '店舗名'] # ヘッダカラムを除去
        for _, row in df.iterrows():
            item = ShopItem()
            item['shop_name'] = row['店舗名'].strip()
            item['address'] = row['所在地'].strip()
            item['genre_name'] = '飲食店' # 鹿児島のPDFにはジャンルがないので
            yield item

        pathlib.Path(tmp_csv)
        pathlib.Path(tmp_pdf)
