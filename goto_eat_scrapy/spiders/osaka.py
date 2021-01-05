import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class OsakaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl osaka -O osaka.csv
    """
    name = 'osaka'
    allowed_domains = [ 'goto-eat.weare.osaka-info.jp' ] # weareって要る？

    # MEMO: https://goto-eat.weare.osaka-info.jp/gotoeat/ から「すべてのエリア」「すべてのジャンル」で検索した結果。つよい
    start_urls = ['https://goto-eat.weare.osaka-info.jp/gotoeat/?search_element_0_0=2&search_element_0_1=3&search_element_0_2=4&search_element_0_3=5&search_element_0_4=6&search_element_0_5=7&search_element_0_6=8&search_element_0_7=9&search_element_0_8=10&search_element_0_9=11&search_element_0_cnt=10&search_element_1_cnt=17&search_element_2_cnt=1&s_keyword_3=&cf_specify_key_3_0=gotoeat_shop_address01&cf_specify_key_3_1=gotoeat_shop_address02&cf_specify_key_3_2=gotoeat_shop_address03&cf_specify_key_length_3=2&searchbutton=%E5%8A%A0%E7%9B%9F%E5%BA%97%E8%88%97%E3%82%92%E6%A4%9C%E7%B4%A2%E3%81%99%E3%82%8B&csp=search_add&feadvns_max_line_0=4&fe_form_no=0']

    # ジャンルはタグで管理されてるが、エリア名も一緒にタグ扱いとなっているため
    area_list = [
        'キタ',
        'ミナミ',
        '大阪城',
        'あべの・天王寺',
        'ベイエリア',
        '北摂',
        '北河内',
        '中河内',
        '南河内',
        '泉州',
    ]

    # MEMO: 稀に504 Gateway Time-outになるので、DELAYを多めに設定して様子見
    # ただし大阪はそもそも件数が多いので、あまり多くしすぎると時間がかかってしまう
    custom_settings = {
        'DOWNLOAD_DELAY': 4,
    }

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@class="search_result_box"]/ul/li'):
            item = ShopItem()

            shop_name = article.xpath('.//p[@class="name"]/text()').get()
            # MEMO: 2020/11/28現在、「珉珉上新庄駅前店」だけ店名が取れないため例外対応。
            # og:title辺りには出ており、他の「珉珉」では普通に表示される店もあるので、謎…
            # (京橋店はひらがなで「みんみん」となっており、謎は深まっている)
            item['shop_name'] = shop_name.strip() if shop_name else '珉珉上新庄駅前店'

            # ジャンル名
            # MEMO: 複数ジャンルを想定した実装だが、大阪の場合は複数ジャンルが指定されているデータはない(はず)
            genres = []
            for tag in article.xpath('.//ul[@class="tag_list"]/li/text()'):
                tagtext = tag.get().strip()
                if tagtext in self.area_list:
                    # MEMEO: 地名タグも複数指定されていることはない前提(後勝ちで上書きされる)
                    item['area_name'] = tagtext
                    continue
                genres.append(tagtext)
            item['genre_name'] = '|'.join(genres)

            # MEMO: 営業時間、定休日の未入力があるのでテーブルレイアウトを直接指定
            text = article.xpath('.//table/tr[1]/td/text()').getall()
            item['zip_code'] = text[0].strip()
            item['address'] = re.sub(r'\s', '', text[1])
            item['tel'] = article.xpath('.//table/tr[2]/td/text()').get()
            item['opening_hours'] = article.xpath('.//table/tr[3]/td/text()').get()
            item['closing_day'] = article.xpath('.//table/tr[4]/td/text()').get()

            # MEMO: 詳細ページまで回せば公式ページのURLが取れるが、それだけのために15k以上のデータにアクセスすべきとは
            # 思えなかったのでやってない。大阪の場合、2020/11/28現在でも881ページもあるし…
            item['detail_page'] = article.xpath('.//a[contains(text(), "詳しく見る")]/@href').get().strip()

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]//a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
