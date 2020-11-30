import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class YamaguchiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl yamaguchi -O yamaguchi.csv
    """
    name = 'yamaguchi'
    allowed_domains = [ 'gotoeat-yamaguchi.com' ] # .comとは
    start_urls = ['https://gotoeat-yamaguchi.com/use/?post_type=post&s=']

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//ul[@id="shop-list"]/li'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[@class="left"]/h3/a/text()').get().strip()

            genres = article.xpath('.//div[@class="left"]/p[@class="type"]/a/text()').getall()
            item['genre_name'] = '|'.join([g.replace('●', '') for g in genres]) # 複数ジャンル

            item['address'] = article.xpath('.//div[@class="left break"]/p/strong[contains(text(), "［住所］")]/../text()').get().strip()
            item['opening_hours'] = article.xpath('.//div[@class="left break"]/p/strong[contains(text(), "［営業時間］")]/../text()').get().strip()
            item['closing_day'] = article.xpath('.//div[@class="left break"]/p/strong[contains(text(), "［定休日］")]/../text()').get().strip()
            item['tel'] = article.xpath('.//div[@class="left break"]/p/strong[contains(text(), "［TEL］")]/../text()').get()

            # MEMO: 山口県の"rink"は複数指定でき、公式HP以外にも各種SNSアカウント等が登録されているが、とりあえず先頭のものだけ取得している
            item['official_page'] = article.xpath('.//div[@class="rink"]/a[1]/@href').get()

            # MEMO: エリア情報については検索結果に含まれず、検索条件を指定して取得しなければいけないため、現時点では非対応とする

            self.logzero_logger.debug(item)
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')
        yield scrapy.Request(next_page, callback=self.parse)
