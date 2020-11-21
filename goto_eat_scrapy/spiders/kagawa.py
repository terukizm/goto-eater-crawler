import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class KagawaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl kagawa -O 37_kagawa.csv
    """
    name = 'kagawa'
    allowed_domains = [ 'kagawa-gotoeat.com' ]

    start_urls = ['https://www.kagawa-gotoeat.com/gtes/store-list?fstr=&mode=only']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@class="container"]/div[contains(@class, "store-list")]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//h4/text()').get().strip()
            # 複数ジャンルが"｜"(全角)で指定されているので、CSVの複数ジャンル指定の内部表現に合わせて'|'(半角)に置換
            item['genre_name'] = article.xpath('.//table/tr/th/span[contains(text(), "料理ジャンル")]/../following-sibling::td/text()').get().strip().replace('｜', '|')
            item['tel'] = article.xpath('.//table/tr/th/span[contains(text(), "電話番号")]/../following-sibling::td/text()').get().strip()
            item['address'] = article.xpath('.//table/tr/th/span[contains(text(), "住所")]/../following-sibling::td/text()').get().strip()
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
