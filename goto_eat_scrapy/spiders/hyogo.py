import re
import urllib.parse

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class HyogoSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl hyogo -O hyogo.csv
    """

    name = "hyogo"
    allowed_domains = ["gotoeat-hyogo.com"]
    start_urls = ["https://gotoeat-hyogo.com/search/result?keyword="]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//ul[@class="search-results-list"]/li'):
            item = ShopItem()
            item["shop_name"] = article.xpath('.//div/p[@class="search-results-list-name"]/text()').get().strip()

            places = article.xpath('.//span[contains(text(), "住所")]/following-sibling::span/text()').getall()
            item["address"] = re.sub(r"\s", "", places[1])
            item["zip_code"] = places[0].strip().replace("〒", "")

            item["tel"] = article.xpath('.//span[contains(text(), "TEL：")]/following-sibling::span/a/text()').get()

            # MEMO: 詳細ページ中にも「ジャンル」に相当する情報がHTMLに含まれていないため、「ジャンル」を抜いてくる方法がない。
            # (おそらく内部的にはデータとして保持しているが、検索クエリで当てていく以外にその値を取得する方法がない)
            # しかも内部的には複数ジャンルっぽいため(「和食」と「居酒屋・ダイニングバー」の両方でHitしたりする)
            # 結果のマージを考えると非常にめんどくさく、とりあえず兵庫県については「ジャンルなし」で固定とした。
            item["genre_name"] = None

            # MEMO: 詳細ページURLに何故か(ページネーション関係？)で?page=xxxというクエリパラメータがつくが、これによってCSVの差分が発生してしまうので削除
            url = article.xpath('.//div/p[@class="search-results-list-btn"]/a/@href').get().strip()
            parse_result = urllib.parse.urlparse(url)
            item["detail_page"] = url.replace(parse_result.query, "")[:-1]

            yield item

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath(
            '//p[@class="search-results-num current"]/following-sibling::p[@class="search-results-num"]/a/@href'
        ).extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
