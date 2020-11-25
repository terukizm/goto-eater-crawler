
import scrapy
import tabula
import pathlib
import pandas as pd
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class OldHokkaidoSpider(scrapy.Spider):
    """
    かつてはPDFが直置きされていてtabulaで頑張ったが、不要になった…
    PDF系の参照用に残しておく…　(後で消す)

    usage:
      $ scrapy crawl hokkaido -O output.csv
    """
    name = 'hokkaido_old'
    allowed_domains = [ 'gotoeat-hokkaido.jp' ]

    start_urls = [
        'https://gotoeat-hokkaido.jp/image/general/shop_douou.pdf',     # 「道央」 35ページ以上
        'https://gotoeat-hokkaido.jp/image/general/shop_dounan.pdf',    # 「道南」  6ページくらい
        'https://gotoeat-hokkaido.jp/image/general/shop_douhoku.pdf',   # 「道北」  6ページくらい
        'https://gotoeat-hokkaido.jp/image/general/shop_doutou.pdf',    # 「道東」 10ページ以上
    ]

    def _genre(self, genre_name: str):
        # PDFは自由入力されているため、ジャンル名がめちゃめちゃになっているので、ある程度寄せる
        # あとtabulaの解析ミスなのか末尾が切れてるのもあるのでその辺りも補完
        if genre_name in ['すし', '回転すし']:
            return 'すし'
        if genre_name in ['焼肉', 'ホルモン焼', 'ステーキ・鉄板焼', 'ジンギスカン']:
            return '焼肉・ステーキ・鉄板焼'
        if genre_name in ['日本料理・郷土料理', '懐石・割烹', '天ぷら・うなぎ', 'とんかつ', \
            'すきやき・しゃぶしゃぶ', 'かに料理・海鮮料理', 'おにぎり・釜飯', 'もつ焼・おでん', \
            '丼・鍋', 'その他の日本料理']:
            return '和食'
        if genre_name in ['フランス料理・イタリア料理', 'その他の⻄洋料理']:
            return '洋食'
        if genre_name in ['中華料理・台湾料理', 'ぎょうざ']:
            return '中華'
        if genre_name in ['ラーメン・中華そば', 'そば・うどん', 'スパゲティ・パスタ']:
            return '麺類'
        if genre_name in ['アジア・エスニック料理', '韓国料理', '無国籍料理・多国籍料理', 'インド料理・カレー']:
            return 'アジア・エスニック・多国籍料理'
        if genre_name in ['居酒屋・大衆酒場', 'ダイニングバー', 'ビヤホール・ビアレストラン'] \
            or genre_name.startswith('ショットバー') \
            or genre_name.startswith('スナック'):
            return '居酒屋・バー'
        if genre_name in ['カフェ・フルーツパーラー', '喫茶店・珈琲店・紅茶店・茶房', 'ベーカリーカフェ']:
            return 'カフェ・喫茶店'

        # この辺からカテゴライズなんにもわからん…
        if genre_name in ['焼鳥', 'フライドチキン', 'から揚げ・ザンギ']:
            return '焼鳥・フライドチキン・から揚げ・ザンギ'
        if genre_name in ['ハンバーガー', '一般食堂・定食'] \
            or genre_name.startswith('バイキング') \
            or genre_name.startswith('レストラン'):
            return 'レストラン・ファーストフード・バイキング・食堂'
        if genre_name.startswith('イートイン'):
            return 'イートイン'
        if genre_name in ['その他', 'お好み焼き・焼きそば', 'たこ焼き・もんじゃ焼き']:
            return 'その他'

        # それ以外はその他に全部寄せても良いが、一応例外投げて停止するようにした
        # (pdfが更新されたりしたときに新ジャンル追加されて落ちそう...)
        logger.error(f'unknown: {genre_name}')
        raise Exception('不明なジャンル')

    def parse(self, response):
        # PDF中のテキストを全選択して「振興局名」で数えて行数が一致してることを確認 (2020/11/16時点)
        ## 道央
        # $ pbpaste | grep -E '(石狩|空知|後志|胆振|⽇高)' | wc -l
        #      2942
        ## 道南
        # $ pbpaste | grep -E '(檜山|渡島)' | wc -l
        #      462
        ## 道北
        # $ pbpaste | grep -E '(上川|留萌|宗谷)' | wc -l
        #      493
        ## 道東
        # $ pbpaste | grep -E '(オホーツク|十勝|釧路|根室)' | wc -l
        #      774
        # 合計 = 4671

        # MEMO: tabula-pyはtempfile, io.stringIO等ではpd.read_csv()がきちんと動作しなかったので実ファイルに書き込んでいる
        tmp_pdf = f'/tmp/temp_{self.name}.pdf'
        tmp_csv = f'/tmp/temp_{self.name}.csv'
        with open(tmp_pdf, 'wb') as f:
            f.write(response.body)

        tabula.convert_into(tmp_pdf, tmp_csv, output_format="csv", pages='all', lattice=True)
        df = pd.read_csv(tmp_csv, header=1, names=('振興局', '市町村', '店舗名', '住所', '飲食店区分', '電話番号'))
        df = df.dropna(subset=['振興局'])[df['振興局'] != '振興局'] # ヘッダカラムを除去
        for _, row in df.iterrows():
            item = ShopItem()
            item['shop_name'] = row['店舗名']
            item['address'] = row['住所']
            item['genre_name'] = self._genre(row['飲食店区分'])
            item['tel'] = row['電話番号']
            yield item

        pathlib.Path(tmp_csv)
        pathlib.Path(tmp_pdf)
