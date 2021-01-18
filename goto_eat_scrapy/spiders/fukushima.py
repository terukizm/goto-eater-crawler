import re

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class FukushimaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl fukushima -O fukushima.csv
    """

    name = "fukushima"
    allowed_domains = ["gotoeat-fukushima.jp"]
    start_urls = ["https://gotoeat-fukushima.jp/shop/?s="]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//div[@class="block_search-result"]/ul[@class="list_search-result"]/li'):
            item = ShopItem()
            item["shop_name"] = article.xpath('.//a/h3[@class="result-name"]/span/text()').get().strip()
            item["address"] = article.xpath('.//a/p[@class="result-address"]/span/text()').get().strip()
            item["genre_name"] = article.xpath('.//a/p[@class="result-cat"]/span/text()').get().strip()

            item["tel"] = article.xpath(
                './/div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[3]/span[@class="info-text"]/text()'
            ).get()
            item["opening_hours"] = article.xpath(
                './/div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[4]/span[@class="info-text"]/text()'
            ).get()
            item["closing_day"] = article.xpath(
                './/div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[5]/span[@class="info-text"]/text()'
            ).get()
            item["official_page"] = article.xpath(
                './/div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[6]/span[@class="info-text"]/a/@href'
            ).get()

            gmap_url = article.xpath(
                './/div[@class="mfp-hide"]//ul[@class="list_store-info"]/li[@class="map-box"]/iframe[@class="acf-map"]/@src'
            ).get()
            m = re.search("q=(?P<lat>\d+\.\d+)\,(?P<lng>\d+\.\d+)", gmap_url)
            if m:
                item["provided_lat"] = m.group("lat")
                item["provided_lng"] = m.group("lng")

            yield item

        # 「NEXT」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
