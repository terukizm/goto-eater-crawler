import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class GunmaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl gunma -O gunma.csv
    """

    name = "gunma"
    allowed_domains = ["gunma-gotoeat-campaign.com"]

    # サイト上は入力制限で同時に3つまでしかジャンル指定ができないようになっているため、お作法に従うなら制限させた上で
    # クローリングさせればよいのだが、内部実装的にそれでシステム負荷が減るわけでもなさそうなので、行儀が悪いが
    # クエリをいじってジャンル指定なしで検索している(ゆるして)
    # (あと合計件数が合わないのでおそらくカテゴリなしになってるレコードが1件あり(後述)、それの確認も兼ねている)
    start_urls = ["https://gunma-gotoeat-campaign.com/shop/?s=&post_type=shop"]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//section[@id="result"]/article'):
            item = ShopItem()

            genre = article.xpath('.//div[2]/span[@class="shopcat"]/text()').get()
            item["genre_name"] = genre.strip() if genre else None
            item["area_name"] = article.xpath(".//div[1]/span/text()").get().strip()

            item["shop_name"] = article.xpath(".//div[2]/h3/text()").get().strip()
            item["zip_code"] = article.xpath('.//div[2]/p[@class="shopadr"]/span/text()').get()[1:]
            item["address"] = article.xpath('.//div[2]/p[@class="shopadr"]/text()').get().strip()

            # オプション項目
            tel = article.xpath('.//div[2]/p[@class="shoptel"]/text()').get()
            item["tel"] = tel.replace("TEL.", "") if tel else None
            item["official_page"] = article.xpath('.//div[2]/div[@class="shopinfo"]/a[2]/@href').get()

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//*[@id="search_page_outer"]//a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
