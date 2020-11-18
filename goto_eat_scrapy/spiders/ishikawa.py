import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class IshikawaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl ishikawa -O 17_ishikawa.csv
    """
    name = 'ishikawa'
    allowed_domains = [ 'ishikawa-gotoeat-cpn.com' ]    # .comとは

    start_urls = ['https://ishikawa-gotoeat-cpn.com/?cities=&type=&s=&post_type=member_store']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@class="baseW"]/ul[@class="member_list"]/li[@class="member_item"]'):
            item = ShopItem()
            item['genre_name'] = article.xpath('.//div[@class="tag_list"]/div[@class="tag_list_item type"]/text()').get().strip()
            item['shop_name'] = article.xpath('.//h4[@class="name"]/text()').get().strip()
            item['zip_code'] = article.xpath('.//div[@class="address"]/div[@class="post"]/text()').get().strip().replace('〒', '')
            item['address'] = article.xpath('.//div[@class="address"]/p/text()').get().strip()

            tel = article.xpath('.//div[@class="tel"]/text()').get()
            item['tel'] = tel.replace('TEL.', '') if tel else None

            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@class="page_nation"]/a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
