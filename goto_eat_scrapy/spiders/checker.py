import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

"""
* 青森県
* 岩手県(めんどい)
* (秋田)
* 山形
* 福島
* 茨城
* 栃木
* 群馬
* 新潟
* 東京
* 富山
* 石川
* 福井
* 山梨(なんで全角にするん？)
* 長野
* 岐阜
* 静岡(青)
* 静岡
* 愛知
* 三重
* 京都
* 大阪
* 和歌山
* 鳥取
* 広島
* 山口
* 高知
* (福岡)
* 佐賀
* 長崎
* 熊本
* 宮崎
* 沖縄

"""

class ShizuokaSpider(AbstractSpider):
    """
      $ scrapy crawl shizuoka -O shizuoka.csv
    """
    name = 'checker'

    def start_requests(self):
        params = {'Keyword': '', 'Action': 'text_search'}
        yield scrapy.FormRequest('https://gotoeat-fukui.com/shop/search.php', \
            callback=self.search, method='POST', \
            formdata=params)

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@class="areaBox"]/div[@class="areaBox__item"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[@class="content__ttl"]/h5[@class="title"]/text()').get().strip()
            item['genre_name'] = article.xpath('.//div[@class="content__ttl"]/div[@class="hashTag"]/p/text()').get().strip()

            place = article.xpath('.//div[@class="infoArea__item"][1]/div[@class="detail"]/p/text()').get().strip()
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')

            item['tel'] = article.xpath('.//div[@class="infoArea__item"][2]/div[@class="detail"]/p/text()').get()
            item['official_page'] = article.xpath('.//div[@class="infoArea__item"][3]/div[@class="detail"]/p/text()').get()

            # MEMO: エリア情報、営業時間、定休日は詳細ページから取得可能。とりあえずは未対応。
            item['detail_page'] = response.urljoin(article.xpath('.//a[contains(@class, "content")]/@href').get().strip())


            yield item

        # 「次の一覧」がなければ終了
        next_page = response.xpath('//div[@class="areaCont"]/div[@class="btnArea pagination"]/a[@class="btn pgt next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        m = re.match(r"^javascript:jumppage\((?P<page>\d+)\);$", next_page)
        next_page = 'https://gotoeat.s-reserve.com/index.html?freeword=&area=&genre=&pgn={}#shopsearch'.format(m.group('page'))
        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
