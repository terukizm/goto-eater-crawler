import re
import scrapy
import w3lib
import json
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class TokyoSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl tokyo -O tokyo.csv
    """
    name = 'tokyo'
    allowed_domains = [ 'r.gnavi.co.jp' ]

    # 企業サイトなので(それもどうかと思うが…) 一応気を使う
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
        # MEMO: 16k件以上ある → 11/28に見たら23k件超えてた... 詳細ページまで見ないといけないので秒間1件で許して…
    }

    start_urls = [
        # 紙と電子、両方使える店とした(紙しか使えない店はあるが、電子しか使えない店はなさそう)
        'https://r.gnavi.co.jp/area/tokyo/kods17214/rs/?gtet_all=1&resp=1&fwp=%E6%9D%B1%E4%BA%AC%E9%83%BD', # 都内全体、食事券対象店(すべて)
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
                item['offical_page'] = data['b'] + '://' + data['a']

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

        self.logzero_logger.debug(item)
        return item

