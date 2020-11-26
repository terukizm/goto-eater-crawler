import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class KyotoSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl kyoto -O output.csv
    """
    name = 'kyoto'
    allowed_domains = [ 'kyoto-gotoeat.com' ]   # .comとは
    start_urls = ['https://kyoto-gotoeat.com/?s=#keyword']

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//main[@id="main"]//div[@class="store-item"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[@class="name"]/a/text()').get().strip()
            item['genre_name'] = article.xpath('.//table/tr/th[contains(text(), "ジャンル")]/following-sibling::td/text()').get().strip()
            item['address'] = article.xpath('.//table/tr/th[contains(text(), "住所")]/following-sibling::td/text()').get().strip()
            item['tel'] = article.xpath('.//table/tr/th[contains(text(), "電話番号")]/following-sibling::td/text()').get().strip()
            item['offical_page'] = article.xpath('.//table/tr/th[contains(text(), "U R L")]/following-sibling::td/a/@href').get()

            self.logzero_logger.debug(item)
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
