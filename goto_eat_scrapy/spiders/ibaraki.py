import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class IbarakiSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl ibaraki -O output.csv
    """
    name = 'ibaraki'
    allowed_domains = [ 'area34.smp.ne.jp' ]   # 推理の絆...

    limit = 100             # limti=1000まで増やしても叩けるが、オフィシャルの最大値に準拠
    table_id = 27130
    start_urls = [
        f'https://area34.smp.ne.jp/area/table/{table_id}/3jFZ4A/M?detect=%94%BB%92%E8&_limit_{table_id}={limit}&S=%70%69%6D%67%6E%32%6C%62%74%69%6E%64&_page_{table_id}=1'
    ]

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath(f'//table[@id="smp-table-{self.table_id}"]//tr[contains(@class, "smp-row-data")]'):
            item = ShopItem()
            # 「ジャンル」
            # TODO: 何故か居酒屋のジャンルが細かいので集約してもよい
            item['genre_name'] = article.xpath('.//td[1]/text()').get().strip()
            # 「店舗名」
            # (詳細ページまで見れば公式URLが取れるが、推理の絆をあんまり叩きたくないので今回はパス)
            item['shop_name'] = article.xpath('.//td[2]/a/text()').get().strip()
            # 「電話番号」
            item['tel'] = article.xpath('.//td[3]/text()').get()
            # 「住所」
            address1 = article.xpath('.//td[4]/text()').get()
            address2 = article.xpath('.//td[5]/text()').get()
            item['address'] = f'{address1} {address2}'

            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath(f'//table[@class="smp-pager"]//td[@class="smp-page smp-current-page"]/following-sibling::td[1]/a/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
