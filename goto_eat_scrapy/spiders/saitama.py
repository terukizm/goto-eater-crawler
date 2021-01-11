import os
import urllib.parse
import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class SaitamaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl saitama -O saitama.csv
    """

    name = "saitama"
    allowed_domains = ["saitama-goto-eat.com"]

    area_list = [
        "さいたま市西区",
        "さいたま市北区",
        "さいたま市大宮区",
        "さいたま市見沼区",
        "さいたま市中央区",
        "さいたま市桜区",
        "さいたま市浦和区",
        "さいたま市南区",
        "さいたま市緑区",
        "さいたま市岩槻区",
        "川越市",
        "熊谷市",
        "川口市",
        "行田市",
        "秩父市",
        "所沢市",
        "飯能市",
        "加須市",
        "本庄市",
        "東松山市",
        "春日部市",
        "狭山市",
        "羽生市",
        "鴻巣市",
        "深谷市",
        "上尾市",
        "草加市",
        "越谷市",
        "蕨市",
        "戸田市",
        "入間市",
        "朝霞市",
        "志木市",
        "和光市",
        "新座市",
        "桶川市",
        "久喜市",
        "北本市",
        "八潮市",
        "富士見市",
        "三郷市",
        "蓮田市",
        "坂戸市",
        "幸手市",
        "鶴ヶ島市",
        "日高市",
        "吉川市",
        "ふじみ野市",
        "白岡市",
        "北足立郡伊奈町",
        "入間郡三芳町",
        "入間郡毛呂山町",
        "入間郡越生町",
        "比企郡滑川町",
        "比企郡嵐山町",
        "比企郡小川町",
        "比企郡川島町",
        "比企郡吉見町",
        "比企郡鳩山町",
        "比企郡ときがわ町",
        "秩父郡横瀬町",
        "秩父郡皆野町",
        "秩父郡長瀞町",
        "秩父郡小鹿野町",
        "秩父郡東秩父村",
        "児玉郡美里町",
        "児玉郡神川町",
        "児玉郡上里町",
        "大里郡寄居町",
        "南埼玉郡宮代町",
        "北葛飾郡杉戸町",
        "北葛飾郡松伏町",
        "北埼玉郡騎西町",
    ]

    def start_requests(self):
        # 埼玉県は各市区町村の固定htmlをjQueryで読んでるだけ
        # @see https://saitama-goto-eat.com/store.html
        for area in self.area_list:
            yield scrapy.Request(
                url=f"https://saitama-goto-eat.com/store/{area}.html", callback=self.parse, meta={"area_name": area}
            )

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        area_name = response.meta["area_name"]
        for genre in response.xpath('//div[@class="tab_content"]'):
            genre_name = genre.xpath('.//div[@class="aria_genre"]/text()').get().strip()
            for article in genre.xpath('.//div[@class="aria_store_content"]/div[@class="storebox"]'):
                item = ShopItem(
                    area_name=area_name,
                    genre_name=genre_name,
                    shop_name=article.xpath(".//span[1]/text()").get().strip(),
                    # MEMO: span[2]はひととおり見たが一つも入ってない
                    zip_code=article.xpath(".//span[3]/text()").get().strip(),
                    address=article.xpath(".//span[4]/text()").get().strip(),
                    tel=article.xpath(".//span[5]/text()").get(),
                    official_page=article.xpath(".//span[6]/a/@href").get(),
                )

                yield item
