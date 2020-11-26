import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class IbarakiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl ibaraki -O ibaraki.csv
    """
    name = 'ibaraki'
    allowed_domains = [ 'area34.smp.ne.jp' ]   # 推理の絆...

    limit = 100             # 実はlimit=1000まで増やしても叩けるが、サイトから指定可能な最大値に準拠
    table_id = 27130
    start_urls = [
        f'https://area34.smp.ne.jp/area/table/{table_id}/3jFZ4A/M?detect=%94%BB%92%E8&_limit_{table_id}={limit}&S=%70%69%6D%67%6E%32%6C%62%74%69%6E%64&_page_{table_id}=1'
    ]

    # 企業サイトなので(それもどうかと思うが…) 一応気を使う
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 3,
    }

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath(f'//table[@id="smp-table-{self.table_id}"]//tr[contains(@class, "smp-row-data")]'):
            item = ShopItem()
            item['genre_name'] = article.xpath('.//td[1]/text()').get().strip()
            item['shop_name'] = article.xpath('.//td[2]/a/text()').get().strip()

            item['tel'] = article.xpath('.//td[3]/text()').get()

            address1 = article.xpath('.//td[4]/text()').get()
            address2 = article.xpath('.//td[5]/text()').get()
            item['address'] = f'{address1} {address2}'

            # MEMO: 詳細ページまで見れば「公式URL」「定休日」「営業時間」が取れるが、推理の絆をあんまり叩きたくないので今回はパス
            # -> といっても同じ推理の絆を使ってる三重県、岐阜県では(仕方なく)詳細ページまで叩いてるので今更感はある

            self.logzero_logger.debug(item)
            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath(f'//table[@class="smp-pager"]//td[@class="smp-page smp-current-page"]/following-sibling::td[1]/a/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
