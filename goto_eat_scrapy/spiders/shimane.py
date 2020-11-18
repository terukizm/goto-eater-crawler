import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class shimaneSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl shimane -O 32_shimane.csv
    """
    name = 'shimane'
    allowed_domains = [ 'gotoeat-shimane.jp' ]

    start_urls = ['https://www.gotoeat-shimane.jp/inshokuten/']

    def parse(self, response):
        # 詳細ページから各加盟店情報を抽出
        for article in response.xpath('//div[@id="main"]//div[@class="com-location"]/ul/li'):
            url = article.xpath('.//a/@href').get()
            yield scrapy.Request(response.urljoin(url), callback=self.detail)

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@class="pagination"]/span[@class="next"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

    def detail(self, response):
        item = ShopItem()
        item['shop_name'] = response.xpath('//h1[@class="title"]/text()').get().strip()
        item['address'] = response.xpath('//div[@class="info line addr"]/p/text()').get().strip()
        item['offical_page'] = response.xpath('//div[@class="info line url"]/p/text()').get()
        item['genre_name'] = self._genre(response.xpath('//div[@class="info select genre"]/p/span/text()').get().strip())

        tel = response.xpath('//div[@class="info line tel"]/p/text()').get()
        item['tel'] = tel.strip() if tel else None

        yield item

    def _genre(self, genre_name: str):
        # その他のジャンルが多すぎるので集約
        # もしかしたら "その他   \n   (カフェ)"といった書式なのかも
        genre_name = ''.join(genre_name.split())
        if genre_name.startswith('その他'):
            return 'その他'

        return genre_name

        # TODO: レストランあたりは通常ジャンルにしてもいいかもしれない、ただ分類が謎
        #
        # [I 201118 19:20:01 main:121] genre_name=居酒屋
        # [I 201118 19:20:01 main:121] genre_name=和食・日本料理
        # [I 201118 19:20:01 main:121] genre_name=焼肉・ホルモン
        # [I 201118 19:20:01 main:121] genre_name=ラーメン
        # [I 201118 19:20:01 main:121] genre_name=その他（カフェ）
        # [I 201118 19:20:02 main:121] genre_name=定食・食堂
        # [I 201118 19:20:02 main:121] genre_name=その他（古民家カフェ）
        # [I 201118 19:20:02 main:121] genre_name=寿司
        # [I 201118 19:20:02 main:121] genre_name=イタリアン・フレンチ
        # [I 201118 19:20:02 main:121] genre_name=ダイニングバー・バル
        # [I 201118 19:20:02 main:121] genre_name=中華・台湾料理
        # [I 201118 19:20:02 main:121] genre_name=そば・うどん
        # [I 201118 19:20:02 main:121] genre_name=各国料理・多国籍料理
        # [I 201118 19:20:02 main:121] genre_name=その他（ぜんざい）
        # [I 201118 19:20:02 main:121] genre_name=その他（パン）
        # [I 201118 19:20:02 main:121] genre_name=その他（喫茶店）
        # [I 201118 19:20:02 main:121] genre_name=創作料理
        # [I 201118 19:20:02 main:121] genre_name=その他（サラダ屋）
        # [I 201118 19:20:02 main:121] genre_name=お好み焼き・たこ焼き
        # [I 201118 19:20:02 main:121] genre_name=その他（日本茶カフェ）
        # [I 201118 19:20:02 main:121] genre_name=その他（喫茶、軽食）
        # [I 201118 19:20:02 main:121] genre_name=その他（喫茶）
        # [I 201118 19:20:02 main:121] genre_name=その他（茶室）
        # [I 201118 19:20:02 main:121] genre_name=その他（レストラン・寿司・居酒屋）
        # [I 201118 19:20:02 main:121] genre_name=その他（洋風居酒屋）
        # [I 201118 19:20:02 main:121] genre_name=海鮮
        # [I 201118 19:20:02 main:121] genre_name=その他（カフェ・レストラン）
        # [I 201118 19:20:02 main:121] genre_name=その他
        # [I 201118 19:20:02 main:121] genre_name=その他（レストラン）
        # [I 201118 19:20:02 main:121] genre_name=カレー
        # [I 201118 19:20:02 main:121] genre_name=その他（パン・サンドウィッチ・焼菓子）
        # [I 201118 19:20:02 main:121] genre_name=その他（焼肉・しゃぶしゃぶ・居酒屋・食堂））
        # [I 201118 19:20:02 main:121] genre_name=その他（薬膳スープカレー）
        # [I 201118 19:20:02 main:121] genre_name=その他（クラフトビール店）
        # [I 201118 19:20:02 main:121] genre_name=その他（蕎麦、そば前、日本酒）
        # [I 201118 19:20:02 main:121] genre_name=その他（フードコート）
        # [I 201118 19:20:02 main:121] genre_name=その他（和洋島のオリジナル料理）
        # [I 201118 19:20:02 main:121] genre_name=その他（喫茶、甘味）
        # [I 201118 19:20:02 main:121] genre_name=その他（牛たん料理専門店）
        # [I 201118 19:20:02 main:121] genre_name=その他（喫茶・軽食）
        # [I 201118 19:20:02 main:121] genre_name=その他（ベーカリーカフェ）
        # [I 201118 19:20:03 main:121] genre_name=韓国料理
        # [I 201118 19:20:03 main:121] genre_name=その他（ソフトクリーム、コロッケ）
        # [I 201118 19:20:03 main:121] genre_name=その他（ベジタリアン料理）
        # [I 201118 19:20:03 main:121] genre_name=その他（ラーメン、焼きそば、丼、うどん、カレー他）
        # [I 201118 19:20:03 main:121] genre_name=その他（ステーキハウス）
        # [I 201118 19:20:03 main:121] genre_name=その他（ビアガーデン）
        # [I 201118 19:20:03 main:121] genre_name=その他（カフェレストラン）
        # [I 201118 19:20:03 main:121] genre_name=その他（ワイン、喫茶）
        # [I 201118 19:20:03 main:121] genre_name=その他（スイーツ）
        # [I 201118 19:20:03 main:121] genre_name=その他（パン・チョコレート・ケーキ・ドリンク他）
        # [I 201118 19:20:03 main:121] genre_name=その他（フライドチキン）
        # [I 201118 19:20:03 main:121] genre_name=その他（和食・洋食）
        # [I 201118 19:20:03 main:121] genre_name=その他（洋菓子）
        # [I 201118 19:20:03 main:121] genre_name=その他（ファストフード）
        # [I 201118 19:20:03 main:121] genre_name=その他（ファーストフード）
        # [I 201118 19:20:03 main:121] genre_name=その他（ドーナツ）
        # [I 201118 19:20:03 main:121] genre_name=その他（ステーキ）
        # [I 201118 19:20:03 main:121] genre_name=その他（ハンバーガー他）
        # [I 201118 19:20:03 main:121] genre_name=その他（アイスクリーム）
        # [I 201118 19:20:03 main:121] genre_name=その他（ファーストフード(ハンバーガー)）
        # [I 201118 19:20:03 main:121] genre_name=その他（一般食堂）
        # [I 201118 19:20:03 main:121] genre_name=その他（クレープ）
        # [I 201118 19:20:03 main:121] genre_name=その他（スナック（接客を伴わない））
        # [I 201118 19:20:03 main:121] genre_name=その他（ファミリーレストラン）
        # [I 201118 19:20:03 main:121] genre_name=その他（アイス・クレープ）
        # [I 201118 19:20:03 main:121] genre_name=その他（とんかつ）
        # [I 201118 19:20:03 main:121] genre_name=その他（焼き鳥屋）
        # [I 201118 19:20:03 main:121] genre_name=その他（オーセンティックバー）
        # [I 201118 19:20:03 main:121] genre_name=その他（ドリンク・フライドポテト）
        # [I 201118 19:20:03 main:121] genre_name=その他（喫茶・カフェ）
        # [I 201118 19:20:03 main:121] genre_name=その他（珈琲・軽食）
        # [I 201118 19:20:03 main:121] genre_name=その他（焼きとり屋）
        # [I 201118 19:20:03 main:121] genre_name=その他（おばんざい）
        # [I 201118 19:20:03 main:121] genre_name=その他（バイキングレストラン）
        # [I 201118 19:20:03 main:121] genre_name=その他（ガニックカフェ）
        # [I 201118 19:20:03 main:121] genre_name=その他（カフェ、喫茶店）
        # [I 201118 19:20:03 main:121] genre_name=その他（テイクアウト・軽食）
        # [I 201118 19:20:03 main:121] genre_name=その他（アイスクリーム及び喫茶）
        # [I 201118 19:20:03 main:121] genre_name=その他（法要会席、軽食）
        # [I 201118 19:20:03 main:121] genre_name=その他（コーヒービーンズショップ）
        # [I 201118 19:20:03 main:121] genre_name=その他（薬膳料理）
        # [I 201118 19:20:03 main:121] genre_name=その他（ソフトクリーム店）
        # [I 201118 19:20:03 main:121] genre_name=その他（ヴィーガンレストラン）
        # [I 201118 19:20:03 main:121] genre_name=その他（しゃぶしゃぶ店）
        # [I 201118 19:20:03 main:121] genre_name=その他（しゃぶしゃぶ・すき焼き・洋食）
        # [I 201118 19:20:03 main:121] genre_name=その他（とんかつ専門店）
        # [I 201118 19:20:03 main:121] genre_name=その他（コーヒー店）
        # [I 201118 19:20:03 main:121] genre_name=その他（明石焼）
        # [I 201118 19:20:03 main:121] genre_name=その他（うなぎ料理）
        # [I 201118 19:20:03 main:121] genre_name=その他（出雲ぜんざい店）
        # [I 201118 19:20:03 main:121] genre_name=その他（トンカツ）
        # [I 201118 19:20:03 main:121] genre_name=その他（(カフェ・喫茶)）
