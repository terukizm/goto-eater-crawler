
import scrapy
import fitz
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
    allowed_domains = [ 'kagoshima-cci.or.jp' ]
    start_urls = ['http://www.kagoshima-cci.or.jp/?p=20375']

    # FIXME: やっつけがすぎる...
    area_list = [
        '鹿児島市全域',
        '〇薩摩川内市',
        '〇鹿屋市',
        '〇枕崎市',
        '〇阿久根市',
        '〇奄美市',
        '〇南さつま市',
        '〇出水市',
        '〇指宿市',
        '〇いちき串木野市',
        '〇霧島市',
        '〇姶良市',
        '〇その他地域',
    ]
    not_target_area_list = [
        '天文館地区',
        '鹿児島中央駅地区',
        '中央地区',
        '上町地区',
        '鴨池地区',
        '城西地区',
        '武・田上地区',
        '谷山北部地区',
        '谷山地区',
        '伊敷・吉野地区',
        '桜島・吉田・喜入・松元・郡山地区',
        '◇食事券購入情報はこちら',
    ]

    def parse(self, response):
        for p in response.xpath('//div[@id="contents_layer"]/span/p'):
            text = p.xpath('.//a/text()').get()
            if not text:
                continue
            if text in self.not_target_area_list:
                continue
            if text in self.area_list:
                pdf_url = p.xpath('.//a/@href').get().strip()
                yield scrapy.Request(pdf_url, callback=self.parse_from_pdf)
            else:
                # たのむぞkcci...
                self.logzero_logger.warn(f'鹿児島商工会議所エラー: 「{text}」 is not found.')


    def parse_from_pdf(self, response):
        # MEMO: tempfile, io.stringIOではtabula-pyがきちんと動作しなかったので、
        # scrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)に書き込んでいる
        cache_dir = pathlib.Path(__file__).parent.parent.parent / '.scrapy' / settings.HTTPCACHE_DIR / self.name
        prefix = response.request.url.replace('http://www.kagoshima-cci.or.jp/wp-content/uploads/', '').replace('/', '-').replace('.pdf', '')
        tmp_pdf = str(cache_dir / f'{prefix}.pdf')
        with open(tmp_pdf, 'wb') as f:
            f.write(response.body)
        self.logzero_logger.info(f'💾 saved pdf: {response.request.url} > {tmp_pdf}')

        # tabula-py, Camelot, pdfminer, pdfboxと試し、最終的にpymupdfを利用
        # PDFが「罫線なし」「レイアウトが不規則(頭文字があるため)」ということで大変処理がしにくい…
        # さらに「鹿児島市全域」のPDFの場合、鹿児島市が省略されている
        for page in fitz.open(tmp_pdf):
            lines = page.getText("text").split('\n')
            for i, row in enumerate(lines):
                if row.startswith('検索'):
                    item = ShopItem()
                    item['shop_name'] = row.replace('検索 ', '')
                    item['address'] = '鹿児島市{}'.format(lines[i+1]) if tmp_pdf.endswith('0.pdf') else lines[i+1]
                    item['genre_name'] = None   # 鹿児島のPDFはジャンル情報なし
                    self.logzero_logger.debug(item)
                    yield item

        # MEMO: 雑なPDFと行数を突き合わせての結果確認
        #
        # ブラウザでクリップボードに全選択したあとに
        # $ pbpaste | grep 検索 | wc -l
        # 1466

        ### 2020/11/30時点で
        # 1466 + 146 + 146 + 34 + 42 + 139 + 65 + 101 + 104 + 50 + 174 + 74 + 145
        # = 2686
