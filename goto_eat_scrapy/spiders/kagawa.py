import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class KagawaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl kagawa -O kagawa.csv
    """

    name = "kagawa"
    allowed_domains = ["kagawa-gotoeat.com"]
    start_urls = ["https://www.kagawa-gotoeat.com/gtes/store-list?fstr=&mode=only"]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//div[@class="container"]/div[contains(@class, "store-list")]'):
            item = ShopItem()
            item["shop_name"] = article.xpath(".//h4/text()").get().strip()
            item["area_name"] = (
                article.xpath('.//table/tr/th/span[contains(text(), "エリア")]/../following-sibling::td/text()')
                .get()
                .strip()
            )

            # 複数ジャンルの場合があり、区切り文字が "｜"(全角パイプ) で指定されている
            # CSVの複数ジャンル指定時の内部表現に合わせて "|"(半角パイプ) に置換
            genre = article.xpath(
                './/table/tr/th/span[contains(text(), "料理ジャンル")]/../following-sibling::td/text()'
            ).get()
            item["genre_name"] = genre.strip().replace("｜", "|")

            item["tel"] = (
                article.xpath('.//table/tr/th/span[contains(text(), "電話番号")]/../following-sibling::td/text()')
                .get()
                .strip()
            )
            item["address"] = (
                article.xpath('.//table/tr/th/span[contains(text(), "住所")]/../following-sibling::td/text()')
                .get()
                .strip()
            )

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]/a[@rel="next"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        next_page = response.urljoin(next_page)
        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
