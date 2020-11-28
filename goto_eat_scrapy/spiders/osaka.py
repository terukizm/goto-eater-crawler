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

    # ジャンルはタグで管理されてるが、地域名(泉州とか)も一緒にタグ管理されているので
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

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for li in response.xpath('//div[@class="search_result_box"]/ul/li'):
            item = ShopItem()
            # MEMO: 2020/11/28現在、珉珉上新庄駅前店だけ店名が取れない、文字コード関係？
            item['shop_name'] = li.xpath('.//p[@class="name"]/text()').get()

            # ジャンル名
            # MEMO: 複数ジャンルを想定した実装だが、大阪の場合は複数ジャンルが指定されているのデータはない(はず)
            genres = []
            for tag in li.xpath('.//ul[@class="tag_list"]/li/text()'):
                tagtext = tag.get().strip()
                if tagtext in self.area_list:
                    # 地名タグの場合はskip
                    continue
                genres.append(tagtext)
            item['genre_name'] = '|'.join(genres)

            text = li.xpath('.//table/tr[1]/td/text()').getall()
            item['zip_code'] = text[0].strip()
            item['address'] = re.sub(r'\s', '', text[1])
            item['tel'] = li.xpath('.//table/tr[2]/td/text()').get()
            item['opening_hours'] = li.xpath('.//table/tr[3]/td/text()').get()
            item['closing_day'] = li.xpath('.//table/tr[4]/td/text()').get()

            # MEMO: 詳細ページまで回せば公式ページのURLが取れるが、それだけのために15k以上のデータにアクセスすべきとは
            # 思えなかったのでやってない。大阪の場合、2020/11/28現在でも881ページもあるし…
            self.logzero_logger.debug(item)
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]//a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
