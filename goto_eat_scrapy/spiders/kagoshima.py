
import scrapy
import tabula
import pathlib
import pandas as pd
from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class KagoshimaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl kagoshima -O kagoshima.csv
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

    def __init__(self, logfile=None, *args, **kwargs):
        super().__init__(logfile, *args, **kwargs)

    def parse(self, response):
        # TODO: 実際にPDFデータと行数を突き合わせての結果確認

        # MEMO: tempfile, io.stringIOではtabula-pyがきちんと動作しなかったので、
        # scrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)に書き込んでいる
        cache_dir = pathlib.Path(__file__).parent.parent.parent / '.scrapy' / settings.HTTPCACHE_DIR / self.name
        prefix = response.request.url.replace('http://www.kagoshima-cci.or.jp/wp-content/uploads/', '').replace('/', '-').replace('.pdf', '')
        tmp_pdf = str(cache_dir / f'{prefix}.pdf')
        tmp_csv = str(cache_dir / f'{prefix}.csv')
        with open(tmp_pdf, 'wb') as f:
            f.write(response.body)
        self.logzero_logger.info(f'💾 saved pdf: {response.request.url} > {tmp_pdf}')

        tabula.convert_into(tmp_pdf, tmp_csv, output_format="csv", pages='all', lattice=True)
        self.logzero_logger.info(f'💾 converted csv: {tmp_pdf} > {tmp_csv}')

        df = pd.read_csv(tmp_csv, header=1, names=('店舗名', '所在地'))
        df = df.dropna(subset=['店舗名'])[df['店舗名'] != '店舗名'] # ヘッダ行に相当する部分を除去
        for _, row in df.iterrows():
            item = ShopItem()
            item['shop_name'] = row['店舗名'].strip()
            item['address'] = row['所在地'].strip()
            item['genre_name'] = None   # 鹿児島のPDFはジャンル情報なし
            self.logzero_logger.debug(item)
            yield item
