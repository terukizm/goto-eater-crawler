import re

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class NiigataSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl niigata -O niigata.csv
    """

    name = "niigata"
    allowed_domains = ["niigata-gte.com"]
    start_urls = ["https://niigata-gte.com/shop/"]

    area_list = [
        "新潟市北区",
        "新潟市東区",
        "新潟市中央区",
        "新潟市江南区",
        "新潟市秋葉区",
        "新潟市南区",
        "新潟市西区",
        "新潟市西蒲区",
        "長岡市",
        "三条市",
        "柏崎市",
        "新発田市",
        "小千谷市",
        "加茂市",
        "十日町市",
        "見附市",
        "村上市",
        "燕市",
        "糸魚川市",
        "妙高市",
        "五泉市",
        "上越市",
        "阿賀野市",
        "佐渡市",
        "魚沼市",
        "南魚沼市",
        "胎内市",
        "聖籠町",
        "弥彦村",
        "田上町",
        "阿賀町",
        "出雲崎町",
        "湯沢町",
        "津南町",
        "刈羽村",
        "関川村",
        "粟島浦村",
    ]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//div[@id="result"]/div[@class="cont"]'):
            item = ShopItem()
            item["shop_name"] = "".join(article.xpath(".//h4/text() | .//h4/a/text()").getall()).strip()
            item["official_page"] = article.xpath(".//h4/a/@href").get()

            place = "".join(article.xpath('.//p[@class="add"]/text()').getall()).strip()
            m = re.match(r"〒(?P<zip_code>.*?)\s(?P<address>.*)", place)
            item["address"] = m.group("address")
            item["zip_code"] = m.group("zip_code")
            item["tel"] = article.xpath('.//p[@class="tel"]/text()').get()

            # 新潟県は「地域名」と「ジャンル名」がタグで一緒になっているため、ジャンル名だけを取得
            genres = []
            for tag in article.xpath('.//div[@class="tag"]/span/text()'):
                tagtext = tag.get().strip()
                if not tagtext:
                    continue
                if tagtext in self.area_list:
                    # MEMO: 地域名タグは複数指定されていない前提(もしあれば、後勝ちで上書きされてしまうので注意)
                    item["area_name"] = tagtext
                    continue
                genres.append(tagtext)
            item["genre_name"] = "|".join(genres)

            gmap_url = article.xpath('.//p[@class="add"]/span/a/@href').get() or ""
            m = re.search("\/@(?P<lat>\d+\.\d+)\,(?P<lng>\d+\.\d+)\,", gmap_url)
            if m:
                item["provided_lat"] = m.group("lat")
                item["provided_lng"] = m.group("lng")

            yield item

        # 「次へ」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@id="pagination"]/ul/li[@class="next"]/a/@onclick').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        m = re.match(r"^mySubmit\('(?P<page>.*)'\);$", next_page)
        next_page = m.group("page")
        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
