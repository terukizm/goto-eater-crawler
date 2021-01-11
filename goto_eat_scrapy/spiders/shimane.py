import re
import urllib.parse

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class ShimaneSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl shimane -O shimane.csv
    """

    name = "shimane"
    allowed_domains = ["gotoeat-shimane.jp"]
    start_urls = ["https://www.gotoeat-shimane.jp/inshokuten/"]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//div[@id="main"]//div[@class="com-location"]/ul/li'):
            url = article.xpath(".//a/@href").get()
            yield scrapy.Request(response.urljoin(url), callback=self.detail)

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath(
            '//nav[@class="pagination"]/span[@class="next"]/a[@rel="next"]/@href'
        ).extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        next_page = response.urljoin(next_page)
        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)

    def detail(self, response):
        self.logzero_logger.info(f"💾 url(detail) = {response.request.url}")
        item = ShopItem()

        # MEMO: 詳細ページに?page=xxxというクエリパラメータがつくが、これによってCSVの差分が発生してしまうので削除
        # (検索一覧画面に戻るときにページネーションを保持するための値っぽい)
        url = response.request.url
        parse_result = urllib.parse.urlparse(url)
        item["detail_page"] = url.replace(parse_result.query, "")[:-1]

        item["area_name"] = (
            response.xpath('//div[contains(@class, "com-location")]/p[contains(@class, "area")]/span/text()')
            .get()
            .strip()
        )

        item["shop_name"] = response.xpath('//h1[@class="title"]/text()').get().strip()
        item["address"] = response.xpath('//div[@class="info line addr"]/p/text()').get().strip()
        item["official_page"] = response.xpath('//div[@class="info line url"]/p/text()').get()
        item["closing_day"] = response.xpath('//div[@class="info holidays"]/p/text()').get()

        genre_name = response.xpath('//div[@class="info select genre"]/p/span/text()').get()
        item["genre_name"] = "".join(genre_name.split()) if genre_name else None

        tel = response.xpath('//div[@class="info line tel"]/p/text()').get()
        item["tel"] = tel.strip() if tel else None

        yield item
