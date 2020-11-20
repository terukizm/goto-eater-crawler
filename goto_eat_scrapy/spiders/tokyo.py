import re
import scrapy
import w3lib
import json
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class TokyoSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl tokyo -O 13_tokyo.csv
    """
    name = 'tokyo'
    allowed_domains = [ 'r.gnavi.co.jp' ]

    # 企業サイトなので(それもどうかと思うが…) 一応気を使う
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 3,
        # 'LOG_LEVEL': 'INFO',
    }

    start_urls = [
        # 紙とデジタル両方使える方だけとした
        # 'https://r.gnavi.co.jp/area/tokyo/kods17214/rs/?sc_lid=gtetokyo_top_search_analog', # 都内全体
        # 'https://r.gnavi.co.jp/area/areal2228/kods17214/rs/?resp=1&fwp=%E9%8C%A6%E7%B3%B8%E7%94%BA%E3%83%BB%E6%8A%BC%E4%B8%8A%E3%83%BB%E6%96%B0%E5%B0%8F%E5%B2%A9', # 錦糸町
        'https://r.gnavi.co.jp/area/areal2273/kods17214/rs/?gtet_all=1&resp=1&fwp=%E5%BA%9C%E4%B8%AD%E3%83%BB%E8%AA%BF%E5%B8%83', # 調布
    ]

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@class="result-cassette__wrapper result-cassette__wrapper--normal"]/ul[@class="result-cassette__list"]/li'):
            url = article.xpath('.//div[@class="result-cassette__box"]//a[@class="result-cassette__box-title js-measure"]/@href').get()
            yield scrapy.Request(url, callback=self.detail)

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav//li[@class="pagination__arrow-item"]/a[@class="pagination__arrow-item-inner pagination__arrow-item-inner-next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

    def detail(self, response):
        item = ShopItem()
        logger.debug(response.url) # TODO: 東京に限らず、csvにdetailのurl、入れてやるほうがいいかもしれない
        for tr in response.xpath('//div[@id="info-table"]/table/tbody'):
            item['shop_name'] = tr.xpath('.//tr/th[contains(text(), "店名")]/following-sibling::td/p[@id="info-name"]/text()').get().strip()
            item['tel'] = tr.xpath('.//tr/th[contains(text(), "電話番号・FAX")]/following-sibling::td/ul/li/span[@class="number"]/text()').get()

            # data-oに入ってる謎json？をparse
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

        ## ジャンル算出
        # "header-meta-gen-desc"があればそちらをジャンルとして利用(複数ジャンルが設定されている)
        genre_list = []
        for genre in response.xpath('//header[@role="banner"]//dd[@id="header-meta-gen-desc"]/ol/li'):
            genre_list.append(genre.xpath('.//a/text()').get().strip())
        if genre_list:
            item['genre_name'] = '|'.join(genre_list)
        else:
            # "header-meta-gen-desc"がない場合は以下を利用(単一)
            # TODO: こちらを利用する場合、ジャンル分けがまったく整理されてないので(鬼畜)　csv2geojsonの方できちんとジャンルの名寄せをやること
            item['genre_name'] = response.xpath('//header[@role="banner"]//dd[@id="header-meta-cat-desc"]/text()').get().strip()


        return item

