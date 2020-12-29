import re
import scrapy
import w3lib
import json
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class TokyoGnaviSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl tokyo_gnavi -O tokyo.csv
    """
    name = 'tokyo_gnavi'
    allowed_domains = [ 'r.gnavi.co.jp' ]

    # 企業サイトなので(それもどうかと思うが…) 一応気を使う
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
        # MEMO: 16k件以上ある → 11/28に見たら23k件超えてた → 12/29に見たら32k超え...
        # 詳細ページまで見ないといけないので秒間1件で許して…
    }

    start_urls = [
        # 食事券対象店(すべて)を対象とする
        # MEMO: 都内全体だと31k(12/12現在)くらいあるので、自分用の場合は特定エリアだけに絞って実行するとよい

        # 都内全体
        'https://r.gnavi.co.jp/area/tokyo/kods17214/rs/?gtet_all=1&resp=1&fwp=%E6%9D%B1%E4%BA%AC%E9%83%BD',   # 東京都

        # # 個別地域
        # 'https://r.gnavi.co.jp/area/areal2101/kods17214/rs/?gtet_all=1',    # 銀座・有楽町・築地
        # 'https://r.gnavi.co.jp/area/areal2107/kods17214/rs/?gtet_all=1',    # 新橋・浜松町・田町
        # 'https://r.gnavi.co.jp/area/areal2133/kods17214/rs/?gtet_all=1',    # 赤坂・六本木・麻布
        # 'https://r.gnavi.co.jp/area/areal2184/kods17214/rs/?gtet_all=1',    # 飯田橋・四ツ谷・神楽坂
        # 'https://r.gnavi.co.jp/area/areal2115/kods17214/rs/?gtet_all=1',    # 新宿・代々木
        # 'https://r.gnavi.co.jp/area/areal2116/kods17214/rs/?gtet_all=1',    # 大久保・高田馬場
        # 'https://r.gnavi.co.jp/area/areal2125/kods17214/rs/?gtet_all=1',    # 渋谷・原宿・青山
        # 'https://r.gnavi.co.jp/area/areal2156/kods17214/rs/?gtet_all=1',    # 池袋・巣鴨・駒込
        # 'https://r.gnavi.co.jp/area/areal2141/kods17214/rs/?gtet_all=1',    # 東京駅・丸の内・日本橋
        # 'https://r.gnavi.co.jp/area/areal2198/kods17214/rs/?gtet_all=1',    # 上野・浅草・日暮里
        # 'https://r.gnavi.co.jp/area/areal2142/kods17214/rs/?gtet_all=1',    # 神田・秋葉原・水道橋
        # 'https://r.gnavi.co.jp/area/areal2169/kods17214/rs/?gtet_all=1',    # 品川・五反田・大崎
        # 'https://r.gnavi.co.jp/area/areal2170/kods17214/rs/?gtet_all=1',    # お台場・豊洲・湾岸
        # 'https://r.gnavi.co.jp/area/areal2178/kods17214/rs/?gtet_all=1',    # 恵比寿・中目黒・目黒
        # 'https://r.gnavi.co.jp/area/areal2164/kods17214/rs/?gtet_all=1',    # 自由が丘・三軒茶屋・二子玉川
        # 'https://r.gnavi.co.jp/area/areal2207/kods17214/rs/?gtet_all=1',    # 下北沢・明大前・成城学園前
        # 'https://r.gnavi.co.jp/area/areal2217/kods17214/rs/?gtet_all=1',    # 中野・吉祥寺・三鷹
        # 'https://r.gnavi.co.jp/area/areal2222/kods17214/rs/?gtet_all=1',    # 練馬・江古田・田無
        # 'https://r.gnavi.co.jp/area/areal2228/kods17214/rs/?gtet_all=1',    # 錦糸町・押上・新小岩
        # 'https://r.gnavi.co.jp/area/areal2146/kods17214/rs/?gtet_all=1',    # 人形町・門前仲町・葛西
        # 'https://r.gnavi.co.jp/area/areal2241/kods17214/rs/?gtet_all=1',    # 北千住・綾瀬・亀有
        # 'https://r.gnavi.co.jp/area/areal2250/kods17214/rs/?gtet_all=1',    # 板橋・成増・赤羽
        # 'https://r.gnavi.co.jp/area/areal2254/kods17214/rs/?gtet_all=1',    # 大井町・大森・蒲田
        # 'https://r.gnavi.co.jp/area/areal2273/kods17214/rs/?gtet_all=1',    # 府中・調布
        # 'https://r.gnavi.co.jp/area/areal2923/kods17214/rs/?gtet_all=1',    # 町田・多摩
        # 'https://r.gnavi.co.jp/area/areal2278/kods17214/rs/?gtet_all=1',    # 小金井・国分寺・国立
        # 'https://r.gnavi.co.jp/area/areal2286/kods17214/rs/?gtet_all=1',    # 立川・八王子・青梅
        # 'https://r.gnavi.co.jp/area/aream2295/kods17214/rs/?gtet_all=1',    # 伊豆諸島・小笠原諸島
    ]

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@class="result-cassette__wrapper result-cassette__wrapper--normal"]/ul[@class="result-cassette__list"]/li'):
            url = article.xpath('.//div[@class="result-cassette__box"]//a[@class="result-cassette__box-title js-measure"]/@href').get()
            yield scrapy.Request(url, callback=self.detail)

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav//li[@class="pagination__arrow-item"]/a[@class="pagination__arrow-item-inner pagination__arrow-item-inner-next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

    def detail(self, response):
        item = ShopItem()
        self.logzero_logger.info(f'💾 url(detail) = {response.request.url}')
        item['detail_page'] = response.request.url
        item['area_name'] = response.xpath('//ol[@id="gn_info-breadcrumbs-inner"]/li/a[contains(text(), "東京")]/../following-sibling::li/a/text()').extract_first()
        for tr in response.xpath('//div[@id="info-table"]/table/tbody'):
            item['shop_name'] = tr.xpath('.//tr/th[contains(text(), "店名")]/following-sibling::td/p[@id="info-name"]/text()').get().strip()
            item['tel'] = tr.xpath('.//tr/th[contains(text(), "電話番号・FAX")]/following-sibling::td/ul/li/span[@class="number"]/text()').get()

            # data-oに入ってる謎json？をparseしてURLを組み立て
            data_o = tr.xpath('.//tr/th[contains(text(), "お店のホームページ")]/following-sibling::td/ul/li/a[@class="url go-off"]/@data-o').get()
            if data_o:
                data = json.loads(data_o)
                item['official_page'] = data['b'] + '://' + data['a']

            zip_code = tr.xpath('.//tr/th[contains(text(), "住所")]/following-sibling::td/p[@class="adr slink"]/text()').get()
            item['zip_code'] = zip_code.strip().replace('〒', '') if zip_code else None
            item['address'] = tr.xpath('.//tr/th[contains(text(), "住所")]/following-sibling::td/p[@class="adr slink"]/span[@class="region"]/text()').get().strip()

            text = tr.xpath('.//tr/th[contains(text(), "営業時間")]/following-sibling::td/div/text()').get()
            item['opening_hours'] = w3lib.html.remove_tags(text).strip() if text else None
            texts = tr.xpath('.//tr/th[contains(text(), "定休日")]/following-sibling::td/ul/li/text()').getall()
            item['closing_day'] = '\n'.join(texts)

        ## ジャンル抽出
        # "header-meta-gen-desc"があればそちらをジャンルとして利用(複数ジャンルあり)
        genre_list = []
        for genre in response.xpath('//header[@role="banner"]//dd[@id="header-meta-gen-desc"]/ol/li'):
            genre_list.append(genre.xpath('.//a/text()').get().strip())
        if genre_list:
            item['genre_name'] = '|'.join(genre_list)
        else:
            # "header-meta-gen-desc"がない場合は以下を利用
            # MEMO: こちらを利用する場合、ジャンル分けが自由入力なのでcsv2geojsonの方できちんとジャンルの名寄せをやる必要がある(やった)
            # それでもアホみたいなジャンルが多数設定されているが、そういうのはしょうがない…
            item['genre_name'] = response.xpath('//header[@role="banner"]//dd[@id="header-meta-cat-desc"]/text()').get().strip()

        # (こっそりlat, lngを取る)
        src = response.xpath('//a[@id="info-table-map-img"]/p[@class="figure"]/img/@src').extract_first()
        m = re.search(r'(.*)marker_ns\.png%7C(?P<lat>.*)\,(?P<lng>.*?)\&(.*)', src)
        item['provided_lat'] = m.group('lat')
        item['provided_lng'] = m.group('lng')


        return item

