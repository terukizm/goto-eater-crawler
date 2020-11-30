import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class OkayamaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl okayama -O okayama.csv
    """
    name = 'okayama'
    allowed_domains = [ 'gotoeat-okayama.com' ] # .comとは

    def start_requests(self):
        params = {'c': 'list', 'keyword': '', 'AREA': '', 'BUSINESS': ''}
        self.logzero_logger.info(f'💾 params = {params}')
        yield scrapy.FormRequest('https://gotoeat-okayama.com/shop/index.cgi', \
                callback=self.parse, method='POST', \
                formdata=params)


    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@id="shop"]/div[@class="container"]/div[@class="box"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//p/text()').get().strip()
            item['area_name'] = article.xpath('.//dl/dt[contains(text(), "エリア")]/following-sibling::dd/text()').get().strip()
            item['genre_name'] = article.xpath('.//dl/dt[contains(text(), "業種")]/following-sibling::dd/text()').get().strip()
            item['tel'] = article.xpath('.//dl/dt[contains(text(), "電話番号")]/following-sibling::dd/a[@class="tellink"]/text()').get()
            item['address'] = article.xpath('.//dl/dt[contains(text(), "住所")]/following-sibling::dd/text()').get().strip()
            item['offical_page'] = article.xpath('.//dl/dt[contains(text(), "URL")]/following-sibling::dd/a/@href').get()

            self.logzero_logger.debug(item)
            yield item

        # 「>>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@id="pager"]/ul/li/a[contains(text(),">>")]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

