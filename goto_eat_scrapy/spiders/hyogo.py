import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class HyogoSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl hyogo -O 28_hyogo.csv
    """
    name = 'hyogo'
    allowed_domains = [ 'gotoeat-hyogo.com' ]    # .comとは

    start_urls = ['https://gotoeat-hyogo.com/search/result?keyword=']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//ul[@class="search-results-list"]/li'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div/p[@class="search-results-list-name"]/text()').get().strip()

            places = article.xpath('.//span[contains(text(), "住所")]/following-sibling::span/text()').getall()
            item['address'] = re.sub(r'\s', '', places[1])
            item['zip_code'] = places[0].strip().replace('〒', '')
            item['tel'] = article.xpath('.//span[contains(text(), "TEL：")]/following-sibling::span/a/text()').get()

            # MEMO: 詳細ページ中にもジャンルに相当する情報がHTMLに含まれていないので、抜いてくる方法がない。
            # 複数ジャンルっぽいため、検索クエリからループで回すのもマージがしんどく、とりあえず兵庫はジャンルなし固定とした。
            item['genre_name'] = None

            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//p[@class="search-results-num current"]/following-sibling::p[@class="search-results-num"]/a/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
