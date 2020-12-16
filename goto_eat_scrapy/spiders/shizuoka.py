import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class ShizuokaSpider(AbstractSpider):
    """
    通称: 赤券の方

    usage:
      $ scrapy crawl shizuoka -O shizuoka.csv
    """
    name = 'shizuoka'
    allowed_domains = [ 'gotoeat.s-reserve.com' ]   # .comとは
    start_urls = ['https://gotoeat.s-reserve.com/']

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
