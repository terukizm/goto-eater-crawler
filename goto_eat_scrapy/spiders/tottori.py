import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class TottoriSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl tottori -O 31_tottori.csv
    """
    name = 'tottori'
    allowed_domains = [ 'tottori-gotoeat.jp' ]

    start_urls = [
        'https://tottori-gotoeat.jp/store_list/',
    ]

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@class="row"]//div[contains(@class, "store-list_v2")]'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[1]/h2[contains(@class, "mr-3")]/text()').get().strip()

            # MEMO: (2020/11/22) 理由はわからないが、公式サイトでも検索するとページにまたがって同じデータが出てくるものがある
            # 例: そば処井田農園(P.5〜P.7)
            # 例: ミニレストキューピット(P.6〜P.7)
            # これらが重複レコードしてカウントされてしまうが、公式サイト側でもそう表示されてしまうので(理由は謎…) 対処方法がない。
            # 店名だけで検索すると重複データは出てこないので、なんらかのアプリ側の不具合っぽい気がするが、謎…

            # 以下は今後入れてもよいかも、という項目
            # area: article.xpath('.//div[1]/p[1]/span[@class="icon-area"]/text()').get().strip()
            # comment: article.xpath('.//div[1]/p[2]/text()').get()

            item['address'] = article.xpath('.//div[2]/p/text()').get().strip()
            item['tel'] = article.xpath('.//div[2]/div[@class="d-flex"]/a/@href').get()

            genres = article.xpath('.//p[@class="mb-0"]/span[contains(@class, "icon-genre")]/text()').getall()
            item['genre_name'] = '|'.join(genres)

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@role="navigation"]/div[@class="nav-links"]/a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
