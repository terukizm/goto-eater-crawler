import re

import scrapy
import w3lib

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class ShizuokaBlueSpider(AbstractSpider):
    """
    通称: 青券の方

    usage:
      $ scrapy crawl shizuoka_blue -O shizuoka.csv
    """

    name = "shizuoka_blue"
    allowed_domains = ["gotoeat-shizuoka.com"]
    start_urls = ["https://gotoeat-shizuoka.com/shop/"]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//ul[@id="shop_list"]/li[@class="shop_box"]'):
            item = ShopItem()
            item["shop_name"] = article.xpath('.//h2[@class="shop_name"]/text()').get().strip()

            area_name = article.xpath('.//span[@class="shop_area"]/text()').get().strip()
            item["area_name"] = re.sub(r"【|】", "", area_name)
            genres = article.xpath('.//span[@class="shop_genre"]/text()').getall()
            item["genre_name"] = "|".join(genres)
            zip_code = article.xpath('.//dl[@class="accordion"]//table//span[@class="shop_zip"]/text()').get()
            item["zip_code"] = zip_code.replace("〒", "") if zip_code else None
            address = article.xpath(
                './/dl[@class="accordion"]//table/tr/th[contains(text(), "住所")]/following-sibling::td/text()'
            ).getall()
            item["address"] = "".join([w3lib.html.remove_tags(x.strip()) for x in address])

            item["tel"] = article.xpath(
                './/dl[@class="accordion"]//table/tr/th[contains(text(), "電話番号")]/following-sibling::td/text()'
            ).get()
            item["opening_hours"] = article.xpath(
                './/dl[@class="accordion"]//table/tr/th[contains(text(), "営業時間")]/following-sibling::td/text()'
            ).get()
            item["closing_day"] = article.xpath(
                './/dl[@class="accordion"]//table/tr/th[contains(text(), "定休日")]/following-sibling::td/text()'
            ).get()
            item["official_page"] = article.xpath(
                './/dl[@class="accordion"]/dd/a[@class="btn_link btn__shop_link"]/@href'
            ).get()

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.logzero_logger.info(f"🛫 next url = {next_page}")
        yield scrapy.Request(next_page, callback=self.parse)
