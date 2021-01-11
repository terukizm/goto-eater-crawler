import re

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class YamaguchiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl yamaguchi -O yamaguchi.csv
    """

    name = "yamaguchi"
    allowed_domains = ["gotoeat-yamaguchi.com"]

    def start_requests(self):
        area_list = [
            {"code": "01-shop-area", "name": "岩国エリア"},
            {"code": "02-shop-area", "name": "柳井エリア"},
            {"code": "03-shop-area", "name": "周南エリア"},
            {"code": "04-shop-area", "name": "山口・防府エリア"},
            {"code": "05-shop-area", "name": "萩エリア"},
            {"code": "06-shop-area", "name": "長門エリア"},
            {"code": "07-shop-area", "name": "宇部・小野田・美祢エリア"},
            {"code": "08-shop-area", "name": "下関エリア"},
        ]
        for area in area_list:
            url = "https://gotoeat-yamaguchi.com/use/?post_type=post&s=&cat_area%5B%5D={}".format(area["code"])
            yield scrapy.Request(url, callback=self.parse, meta={"area_name": area["name"]})

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")

        area_name = response.meta["area_name"]
        for article in response.xpath('//ul[@id="shop-list"]/li'):
            item = ShopItem()
            item["shop_name"] = article.xpath('.//div[@class="left"]/h3/a/text()').get().strip()
            item["area_name"] = area_name

            genres = article.xpath('.//div[@class="left"]/p[@class="type"]/a/text()').getall()
            item["genre_name"] = "|".join([g.replace("●", "") for g in genres])  # 複数ジャンルあり

            item["address"] = (
                article.xpath('.//div[@class="left break"]/p/strong[contains(text(), "［住所］")]/../text()').get().strip()
            )
            item["opening_hours"] = (
                article.xpath('.//div[@class="left break"]/p/strong[contains(text(), "［営業時間］")]/../text()')
                .get()
                .strip()
            )
            item["closing_day"] = (
                article.xpath('.//div[@class="left break"]/p/strong[contains(text(), "［定休日］")]/../text()').get().strip()
            )
            item["tel"] = article.xpath(
                './/div[@class="left break"]/p/strong[contains(text(), "［TEL］")]/../text()'
            ).get()

            # MEMO: 山口県の"rink"は複数指定でき、公式HP以外だけでなく、各種SNSアカウント等も登録されているが、とりあえず先頭のものだけを取得している
            item["official_page"] = article.xpath('.//div[@class="rink"]/a[1]/@href').get()

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.logzero_logger.info(f"🛫 next url = {next_page}")
        yield scrapy.Request(next_page, callback=self.parse, meta=response.meta)
