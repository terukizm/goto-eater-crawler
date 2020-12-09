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
            # MEMO: 徳島県は居酒屋っぽい店を「和食」もしくは「その他」でジャンル分けしているため、居酒屋系が1件もない…
            text = ''.join(article.xpath('.//header/text()').getall())
            genre = text.strip().replace('ジャンル：', '')
            item['genre_name'] = '|'.join([s.strip() for s in genre.split(',')])

            item['address'] = article.xpath('.//div[@class="entry-content"]/dl/dt[contains(text(), "所在地")]/following-sibling::dd/text()').get().strip()
            item['closing_day'] = article.xpath('.//div[@class="entry-content"]/dl/dt[contains(text(), "定休日")]/following-sibling::dd/text()').get()
            item['opening_hours'] = article.xpath('.//div[@class="entry-content"]/dl/dt[contains(text(), "営業時間")]/following-sibling::dd/text()').get()
            item['tel'] = article.xpath('.//div[@class="entry-content"]/dl/dt[contains(text(), "電話番号")]/following-sibling::dd/text()').get()

            # MEMO: detailのURLが取れるが、なんとなく一般公開用ではなさそうなので…
            #item['detail_page'] = article.xpath('.//a[@rel="bookmark"]/@href').get().strip()

            # MEMO: 地域名については結果に表示されないので検索条件から抜いてくるしかない
            # (なお地域名、ジャンル名は複数指定するとちゃんと検索できない (2020/12/07))

            self.logzero_logger.debug(item)
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@role="navigation"]/div[@class="nav-links"]/a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
