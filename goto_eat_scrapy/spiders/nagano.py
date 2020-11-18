import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class NaganoSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl nagano -O 20_nagano.csv
    """
    name = 'nagano'
    allowed_domains = [ 'shinshu-gotoeat.com' ]    # .comとは、信州にこだわる意味...？

    start_urls = ['https://shinshu-gotoeat.com/riyou.php']
    page_no = 1

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@class="shop_block"]/div[@class="shop"]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//p[@class="shop_title"]/text()').get().strip()
            item['genre_name'] = article.xpath('.//p[@class="shop_type"]/span[@class="shopgenre"]/text()').get().strip()
            item['address'] = article.xpath('.//p[@class="shop_address"][2]/text()').get().strip().replace('住所：', '')    # classがuniqueでないので注意
            item['tel'] = article.xpath('.//p[@class="shop_tel"]/span/text()').get()
            item['offical_page'] = article.xpath('.//p[@class="shop_tel"]/a/@href').get()
            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@class="pager"]//a[contains(text(),">>")]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.page_no += 1
        next_page = f'https://shinshu-gotoeat.com/riyou.php?p={self.page_no}#search-result'
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
