import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class TottoriSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl tottori -O tottori.csv
    """
    name = 'tottori'
    allowed_domains = [ 'tottori-gotoeat.jp' ]
    start_urls = ['https://tottori-gotoeat.jp/store_list/']

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@class="row"]//div[contains(@class, "store-list_v2")]'):
            item = ShopItem()
            item['area_name'] = article.xpath('.//div[1]/p[1]/span[@class="icon-area"]/text()').get().strip()
            item['shop_name'] = article.xpath('.//div[1]/h2[contains(@class, "mr-3")]/text()').get().strip()

            # MEMO: (2020/11/22) 理由はわからないが、公式サイトでも検索するとページにまたがって同じデータが出てくるものがある
            # これらが重複レコードしてカウントされてしまうが、公式サイト側でもそのように表示されてしまっているので対処方法がない。
            # 店名だけで検索しても重複データは出てこないので、RDBMS側でlimit offsetでページ分けしたときにorder byで指定したソート順の結果が
            # ユニークになっておらず(created_at, updated_atでソートかけてるとかで)同順データが多数ある場合にページが分かれてしまうと、
            # 結果として結果が一意にならない、とかなんじゃないかと思う。内部的にはWPっぽいけどこれ以上はなんとも…

            # MEMO: 店からの一言コメント、妙に好き…
            # comment = article.xpath('.//div[1]/p[2]/text()').get()
            # 他にもテイクアウトの有無など、鳥取は検索オプションが豪華

            item['address'] = article.xpath('.//div[2]/p/text()').get().strip()
            item['tel'] = article.xpath('.//div[2]/div[@class="d-flex"]/a/@href').get()

            genres = article.xpath('.//p[@class="mb-0"]/span[contains(@class, "icon-genre")]/text()').getall()
            item['genre_name'] = '|'.join(genres)

            self.logzero_logger.debug(item)
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@role="navigation"]/div[@class="nav-links"]/a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
