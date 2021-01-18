import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class EhimeSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl ehime -O ehime.csv
    """

    name = "ehime"
    allowed_domains = ["goto-eat-ehime.com"]
    start_urls = ["https://www.goto-eat-ehime.com/shop_list/"]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//div[@id="sortable"]/ul[@class="shop_list"]/li'):
            item = ShopItem()
            item["shop_name"] = article.xpath(".//div/dl/dt/text()").get().strip()
            item["genre_name"] = article.xpath(".//div/p/span/text()").get().strip()
            item["address"] = (
                article.xpath('.//div/dl/dd/ul/li/span[contains(text(), "住所")]/following-sibling::span/text()')
                .get()
                .strip()
            )
            item["tel"] = article.xpath('.//div/dl/dd/ul/li/span/a[@class="tel_link"]/text()').get()

            item["detail_page"] = article.xpath('.//p[@class="btn_link"]/a/@href').get().strip()
            # MEMO: closing_day, opening_hours, official_pageなどを詳細ページから取得可能だが、とりあえず未対応
            # エリアについては検索条件でのみ設定可能なため、結果(一覧/詳細)ページからは取得不可だが、山口県と同様の方式で対応可能

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.logzero_logger.info(f"🛫 next url = {next_page}")
        yield scrapy.Request(next_page, callback=self.parse)
