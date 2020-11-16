import re
import scrapy

from goto_eat_scrapy.items import ShopItem

class IwateSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl iwate -O 03_iwate.csv
    """
    name = 'iwate'
    allowed_domains = [ 'iwate-gotoeat.jp' ]

    area_list = [
        '盛岡市',
        '宮古市',
        '大船渡市',
        '花巻市',
        '北上市',
        '久慈市',
        '遠野市',
        '一関市',
        '陸前高田市',
        '釜石市',
        '二戸市',
        '八幡平市',
        '奥州市',
        '滝沢市',
        '雫石町',
        '葛巻町',
        '岩手町',
        '紫波町',
        '矢巾町',
        '西和賀町',
        '金ケ崎町',
        '平泉町',
        '住田町',
        '大槌町',
        '山田町',
        '岩泉町',
        '田野畑村',
        '普代村',
        '軽米町',
        '野田村',
        '九戸村',
        '洋野町',
        '一戸町',
    ]

    def start_requests(self):
        for area in self.area_list:
            params = {'k': '', 'area': area}
            yield scrapy.FormRequest('https://www.iwate-gotoeat.jp/stores/#search_result', \
                    callback=self.parse, method='POST', \
                    formdata=params)

    def parse(self, response):
        for article in response.xpath('//section[@id="search_result"]//div[@class="stores_box"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//h2[@class="stores_box_name"]/text()').get().strip()
            item['address'] = article.xpath('.//p[@class="stores_box_add"]/text()').get().strip()

            tel = article.xpath('.//p[@class="stores_box_tel"]/text()').get()
            m = re.match(r'.*(?P<tel>0\d{1,4}-\d{1,4}-\d{3,4})', tel)
            item['tel'] = m.group('tel')

            # ジャンル指定が自由入力になっていて地獄 (ジャンル: イカの唐揚げってなんだよ)
            # item['genre_name'] = article.xpath('.//p[@class="stores_box_genre"]/text()').get().strip()

            # TODO: 部分一致くらいで引っ掛けてジャンル分けするしかなさそう...　とりあえず諦めてジャンルなし
            item['genre_name'] = '飲食店'

            yield item
