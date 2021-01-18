import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class NaganoSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl nagano -O nagano.csv
    """

    name = "nagano"
    allowed_domains = ["shinshu-gotoeat.com"]
    start_urls = ["https://shinshu-gotoeat.com/riyou.php"]
    page_no = 1

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//div[@class="shop_block"]/div[@class="shop"]'):
            item = ShopItem()
            item["shop_name"] = article.xpath('.//p[@class="shop_title"]/text()').get().strip()
            item["area_name"] = (
                article.xpath('.//p[@class="shop_type"]/span[@class="shop_shozaichi"]/text()').get().strip()
            )
            item["genre_name"] = article.xpath('.//p[@class="shop_type"]/span[@class="shopgenre"]/text()').get().strip()
            item["address"] = (
                article.xpath('.//p[@class="shop_address"][2]/text()').get().strip().replace("住所：", "")
            )  # class名がuniqueでないので注意
            item["tel"] = article.xpath('.//p[@class="shop_tel"]/span/text()').get()
            item["official_page"] = article.xpath('.//p[@class="shop_tel"]/a/@href').get()

            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@class="pager"]//a[contains(text(),">>")]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.page_no += 1
        next_page = f"https://shinshu-gotoeat.com/riyou.php?p={self.page_no}#search-result"
        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
