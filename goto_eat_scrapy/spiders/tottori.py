import re

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class TottoriSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl tottori -O tottori.csv
    """

    name = "tottori"
    allowed_domains = ["tottori-gotoeat.jp"]
    start_urls = ["https://tottori-gotoeat.jp/store_list/"]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//div[@class="row"]//div[contains(@class, "store-list_v2")]'):
            item = ShopItem()
            item["area_name"] = article.xpath('.//div[1]/p[1]/span[@class="icon-area"]/text()').get().strip()
            item["shop_name"] = article.xpath('.//div[1]/h2[contains(@class, "mr-3")]/text()').get().strip()

            # MEMO: 店からの一言コメント、妙に好き…　他にもテイクアウトの有無など、鳥取は検索オプションが豪華
            # comment = article.xpath('.//div[1]/p[2]/text()').get()

            item["address"] = article.xpath(".//div[2]/p/text()").get().strip()
            item["tel"] = article.xpath('.//div[2]/div[@class="d-flex"]/a[contains(@class, "tel-link")]/@href').get()
            item["official_page"] = article.xpath(
                './/div[2]/div[@class="d-flex"]/a[contains(@target, "_blank")]/@href'
            ).get()

            genres = article.xpath('.//p[@class="mb-0"]/span[contains(@class, "icon-genre")]/text()').getall()
            item["genre_name"] = "|".join(genres)

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath(
            '//nav[@role="navigation"]/div[@class="nav-links"]/a[@class="next page-numbers"]/@href'
        ).extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
