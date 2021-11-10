import re

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class KyotoSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl kyoto -O output.csv
    """

    name = "kyoto"
    allowed_domains = ["kyoto-gotoeat.com"]
    start_urls = ["https://kyoto-gotoeat.com/?s=#keyword"]

    # MEMO: detailまで回すので
    custom_settings = {
        "DOWNLOAD_DELAY": 1.2,
    }

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//main[@id="main"]//div[@class="store-item"]'):
            url = response.urljoin(article.xpath('.//a[@class="btnDetail"]/@href').get().strip())
            yield scrapy.Request(response.urljoin(url), callback=self.detail)

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)

    def detail(self, response):
        self.logzero_logger.info(f"💾 url(detail) = {response.request.url}")
        article = response.xpath('//main[@id="main"]//div[@class="store-detail"]')

        item = ShopItem()
        item["shop_name"] = article.xpath('.//div[@class="name"]/text()').get().strip()
        item["genre_name"] = (
            article.xpath(
                './/div[@class="store-cont"]/table/tr/th[contains(text(), "ジャンル")]/following-sibling::td/text()'
            )
            .get()
            .strip()
        )
        item["area_name"] = (
            article.xpath(
                './/div[@class="store-cont"]/table/tr/th[contains(text(), "エリア")]/following-sibling::td/text()'
            )
            .get()
            .strip()
        )
        item["address"] = (
            article.xpath(
                './/div[@class="store-cont"]/table/tr/th[contains(text(), "住所")]/following-sibling::td/text()'
            )
            .get()
            .strip()
        )
        item["tel"] = (
            article.xpath(
                './/div[@class="store-cont"]/table/tr/th[contains(text(), "電話番号")]/following-sibling::td/text()'
            )
            .get()
        )
        # MEMO: 詳細ページに項目自体はあるが、電話番号、定休日が入ってるデータは1件もない(2021/01/18)
        item["opening_hours"] = article.xpath(
            './/div[@class="store-cont"]/table/tr/th[contains(text(), "営業時間")]/following-sibling::td/text()'
        ).get()
        item["closing_day"] = article.xpath(
            './/div[@class="store-cont"]/table/tr/th[contains(text(), "定休日")]/following-sibling::td/text()'
        ).get()
        item["official_page"] = article.xpath(
            './/div[@class="store-cont"]/table/tr/th[contains(text(), "U R L")]/following-sibling::td/a/@href'
        ).get()

        gmap_url = article.xpath('.//div[@class="store-cont"]/iframe/@src').get()
        m = re.search("q=(?P<lat>\d+\.\d+)\,(?P<lng>\d+\.\d+)", gmap_url)
        if m:
            item["provided_lat"] = m.group("lat")
            item["provided_lng"] = m.group("lng")

        return item
