import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class TokushimaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl tokushima -O tokushima.csv
    """
    name = 'tokushima'
    allowed_domains = [ 'gotoeat.tokushima.jp' ]
    start_urls = ['https://gotoeat.tokushima.jp/?s=']

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//main[@id="main"]//article'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//header/h2/text()').get().strip()

            # 「ジャンル」
            # ","区切りで複数指定してるものがあるので、"|" 区切りに変換
            text = ''.join(article.xpath('.//header/text()').getall())
            genre = text.strip().replace('ジャンル：', '')
            item['genre_name'] = '|'.join([s.strip() for s in genre.split(',')])

            # 2020/11/18時点の暫定実装
            # 本来所在地なしはありえないが、"富田街ダイニング坊乃"を出力したときだけ、DOM構造が崩れている
            # 内部にDOM入りのデータを持っててそのデータがおかしいとか…？
            item['address'] = article.xpath('.//div[@class="entry-content"]/dl/dd[1]/text()').get().strip()

            item['closing_day'] = article.xpath('.//div[@class="entry-content"]/dl/dd[2]/text()').get()
            item['opening_hours'] = article.xpath('.//div[@class="entry-content"]/dl/dd[3]/text()').get()
            item['tel'] = article.xpath('.//div[@class="entry-content"]/dl/dd[4]/text()').get()

            self.logzero_logger.debug(item)
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@role="navigation"]/div[@class="nav-links"]/a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
