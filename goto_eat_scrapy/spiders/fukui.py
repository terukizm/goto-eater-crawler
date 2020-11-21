import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class FukuiSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl fukui -O 18_fukui.csv
    """
    name = 'fukui'
    allowed_domains = [ 'gotoeat-fukui.com' ] # .comとは

    def start_requests(self):
        params = {'Keyword': '', 'Action': 'text_search'}
        yield scrapy.FormRequest('https://gotoeat-fukui.com/shop/search.php', \
            callback=self.search, method='POST', \
            formdata=params)

    def search(self, response):
        for article in response.xpath('//div[@class="result"]/ul/li'):
            url = article.xpath('.//a/@href').get().strip()
            yield scrapy.Request(response.urljoin(url), callback=self.detail)


    def detail(self, response):
        item = ShopItem()
        logger.debug(response.url) # TODO: 福井に限らず、csvにdetailのurl、入れてやるほうがいいかもしれない
        item['shop_name'] = response.xpath('//div[@id="contents"]/h3/text()').get().strip()
        for dl in response.xpath('//div[@id="contents"]/dl'):
            # 複数ジャンル指定あり
            genre_name = dl.xpath('.//dt[contains(text(), "ジャンル")]/following-sibling::dd/text()').get().strip()
            item['genre_name'] = genre_name.replace('、', '|')

            item['tel'] = dl.xpath('.//dt[contains(text(), "電　　話")]/following-sibling::dd/a/text()').get().strip()
            item['address'] = dl.xpath('.//dt[contains(text(), "住　　所")]/following-sibling::dd/text()').get().strip()
            item['opening_hours'] = dl.xpath('.//dt[contains(text(), "営業時間")]/following-sibling::dd/text()').get().strip()
            item['closing_day'] = dl.xpath('.//dt[contains(text(), "定 休 日")]/following-sibling::dd/text()').get().strip()
            item['offical_page'] = dl.xpath('.//dt[contains(text(), "HP・SNS")]/following-sibling::dd/text()').get()

        return item
