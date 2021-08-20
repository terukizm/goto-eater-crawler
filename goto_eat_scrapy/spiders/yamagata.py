import json
import re

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class YamagataSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl yamagata -O yamagata.csv
    """

    name = "yamagata"
    allowed_domains = ["yamagata-gotoeat.com"]

    endpoint = "https://yamagata-gotoeat.com/wp/wp-content/themes/gotoeat/search.php"

    area_list = [
        "山形市",
        "寒河江市",
        "上山市",
        "村山市",
        "天童市",
        "東根市",
        "尾花沢市",
        "山辺町",
        "中山町",
        "河北町",
        "西川町",
        "朝日町",
        "大江町",
        "大石田町",
        "新庄市",
        "金山町",
        "最上町",
        "舟形町",
        "真室川町",
        "大蔵村",
        "鮭川村",
        "戸沢村",
        "米沢市",
        "南陽市",
        "長井市",
        "高畠町",
        "川西町",
        "小国町",
        "白鷹町",
        "飯豊町",
        "酒田市",
        "鶴岡市",
        "三川町",
        "庄内町",
        "遊佐町",
    ]

    def start_requests(self):
        params = {"text": "", "page": "1"}
        yield scrapy.FormRequest(self.endpoint, callback=self.parse, method="POST", formdata=params)

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")

        # レスポンスはjsonなので直接parse
        # (参考): "html"に<li>...</li>が直接入っているので、以下のDOM構造に変換してから、XPathを使って抽出
        #
        # <article>
        #   <li>
        #     <ul class="search__result__tag">
        #       <li>鶴岡市</li>
        #       <li>和食・寿司・天ぷら</li>
        #     </ul>
        #     <h2>和食藤川</h2>    # 公式ページがaタグで入る場合がある
        #     <div>997-0034 山形県鶴岡市本町2-15-27</div>
        #     <div>TEL : 023-522-8821</div>
        #   </li>
        #   <li>....<li>
        #   <li>....<li>
        # </article>
        data = json.loads(response.body)
        html = scrapy.Selector(text="<article>{}</article>".format(data["html"]))
        for article in html.xpath("//article/li"):
            item = ShopItem()
            item["shop_name"] = article.xpath(".//h2/text() | .//h2/a/text()").get().strip()
            item["official_page"] = article.xpath(".//h2/a/@href").get()

            place = article.xpath(".//div[1]/text()").get().strip()
            m = re.match(r"(?P<zip_code>.*?)\s(?P<address>.*)", place)

            if m:
                item["address"] = m.group("address")
                item["zip_code"] = m.group("zip_code")
            else:
                item["address"] = place
                item["zip_code"] = None # MEMO: 2021/08/19 "エノテーカ"に郵便番号がない

            tel = article.xpath(".//div[2]/text()").get()
            item["tel"] = tel.replace("TEL : ", "") if tel else None

            # タグ(ジャンル名、エリア名)
            # MEMO: ジャンル名、エリア名ともに複数指定はないという前提での実装
            for tag in article.xpath('.//ul[@class="search__result__tag"]/li/text()'):
                tagtext = tag.get()
                if not tagtext:
                    continue
                if tagtext in self.area_list:
                    item["area_name"] = tagtext
                    continue
                item["genre_name"] = tagtext

            yield item

        # 一般的なページャ実装のように最終ページを表示させたときに「次へ(最後へ)」リンクが出ないようになってないので、
        # activeのページ=「次へ」リンクのページ　となったときに終了
        pager = scrapy.Selector(text=data["pager"])
        active_page = pager.xpath(
            '//div[@class="search__pager"]/ul/li[@class="search__pager__link active"]/@data-page'
        ).get()
        next_page = pager.xpath('//div[@class="search__pager"]/div[contains(text(),"次へ")]/@data-page').get()

        # (参考): pagerは以下のDOM構造
        #
        # <div class="search__pager">
        #   <div class="search__pager__link seach__pager__small" data-page="1">最初へ</div>
        #   <div class="search__pager__link seach__pager__btn" data-page="1">前へ</div>
        #   <ul>
        #     <li>1</li>
        #     <li class="search__pager__link active" data-page="2">2</li>
        #     <li>...</li>
        #   </ul>
        #   <div class="search__pager__link search__pager__btn" data-page="3">次へ</div>
        #   <div class="search__pager__link seach__pager__small" data-page="85">最後へ</div>
        # </div>

        if active_page == next_page:
            self.logzero_logger.info("💻 finished. last page = " + active_page)
            return

        self.logzero_logger.info(f"next_page = {next_page}")
        params = {"text": "", "page": next_page}
        yield scrapy.FormRequest(self.endpoint, callback=self.parse, method="POST", formdata=params)
