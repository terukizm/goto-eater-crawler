import re

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class TochigiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl tochigi -O tochigi.csv
    """

    name = "tochigi"
    allowed_domains = ["gotoeat-tochigi.jp"]
    start_urls = ["https://www.gotoeat-tochigi.jp/merchant/index.php"]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath(
            '//div[@id="contents"]/ul[@class="serch_result"]/li'
        ):  # MEMO: "serch" is not my TYPO...
            item = ShopItem()
            item["shop_name"] = article.xpath('.//p[@class="name"]/text()').get().strip()
            item["genre_name"] = (
                article.xpath('.//p[@class="name"]/span[contains(@class, "genre")]/text()').get()
            )

            # 「所在地」から「郵便番号」「住所」を取得
            # MEMO: 郵便番号形式にはたまに入力ブレがあるので、正規表現で適当に処理
            place = article.xpath('.//div[@class="add"]/p[1]/text()').get().strip()
            m = re.match(r"〒(?P<zip_code>.*?)\s(?P<address>.*)", place)
            if m:
                item["address"] = m.group("address")
                item["zip_code"] = m.group("zip_code")
            else:
                # MEMO: 「日本海庄や　宇都宮本店」など、郵便番号が入ってない場合がある
                item["address"] = place
                item["zip_code"] = None

            item["tel"] = article.xpath('.//div[@class="add"]/p[2]/a/text()').extract_first()
            item["official_page"] = article.xpath(
                './/ul[@class="hp"]//a[contains(text(),"ホームページ")]/@href'
            ).extract_first()

            # latlng取得
            google_map_url = article.xpath('.//ul[@class="hp"]//a[contains(text(),"GoogleMap")]/@href').extract_first()
            # MEMO: google.co.jpへのリンクとgoogle.comへのリンクが混在
            # 書式もいくつかパターンが混在、latlngが無いやつもある
            m = re.search(r"/maps/.*/@(?P<lat>.*?),(?P<lng>.*?),(?P<zoom>.*)/data", google_map_url)
            if m:
                item["provided_lat"] = m.group("lat")
                item["provided_lng"] = m.group("lng")

            # MEMO: エリア情報は検索結果中に含まれないので、必要なら検索条件として指定する必要がある
            # 山口県同様に実現可能だが、とりあえずは見送り。

            yield item

        # 「次の一覧」がなければ終了
        next_page = response.xpath('//*[@id="contents"]//li[@class="next"]/a/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        next_page = response.urljoin(next_page)
        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
