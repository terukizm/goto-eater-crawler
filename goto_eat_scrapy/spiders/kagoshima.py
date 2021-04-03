import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class KagoshimaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl kagoshima -O kagoshima.csv
    """

    name = "kagoshima"
    allowed_domains = ["kagoshima-cci.or.jp"]
    start_urls = ["http://www.kagoshima-cci.or.jp/?p=20375"]

    # MEMO: 鹿児島は2020/12/04？にpdfをやめてhtmlにしてくれたが、HTMLソースを見ると重複した内容が含まれている。(display:noneで出し分けしてるだけ)
    # ソースコードの内容と件数から見て、おそらく「鹿児島市全域」と「その他地域(鹿屋市〜その他地域)」で２つのExcelファイルがあり、
    # それを(Excelの行の非表示とかで)出し分けし、ExcelのWebページ発行ウィザードで出力していると思われる。
    # 鹿児島はもう3回くらい出力形式が変わっているので、もう諦めてやっつけ仕事でいく...
    area_list = [
        "鹿児島市全域",
        # '〇薩摩川内市',
        # '〇鹿屋市',
        # '〇枕崎市',
        # '〇阿久根市',
        # '〇奄美市',
        # '〇南さつま市',
        # '〇出水市',
        # '〇指宿市',
        # '〇いちき串木野市',
        # '〇霧島市',
        # '〇姶良市',
        "〇その他地域",
    ]
    not_target_area_list = [
        "天文館地区",
        "鹿児島中央駅地区",
        "中央地区",
        "上町地区",
        "鴨池地区",
        "城西地区",
        "武・田上地区",
        "谷山北部地区",
        "谷山地区",
        "伊敷・吉野地区",
        "桜島・吉田・喜入・松元・郡山地区",
        "◇食事券購入情報はこちら",
    ]

    def parse(self, response):
        for p in response.xpath('//div[@id="contents_layer"]/span/p'):
            area_name = p.xpath(".//a/text()").get()
            self.logzero_logger.info(f"🗻 area_name = {area_name}")
            if not area_name:
                continue
            if area_name in self.not_target_area_list:
                continue
            if area_name in self.area_list:
                url = p.xpath(".//a/@href").get().strip()
                yield scrapy.Request(url, callback=self.parse_from_area_html, meta={"area_name": area_name})
            else:
                pass

    def parse_from_area_html(self, response):
        area_name = response.meta["area_name"]
        for article in response.xpath("//table/tr"):
            if article.xpath('.//td[2]//*[contains(text(), "検索")]').get():
                item = ShopItem()
                # MEMO: 店舗名、住所に改行が入ってるものがある(item pipelineで対応)
                item["shop_name"] = article.xpath(".//td[3]/text()").get().strip()
                address = article.xpath("./td[4]/text()").get().strip()
                item["address"] = f"鹿児島市{address}" if area_name == "鹿児島市全域" else address
                # item['genre_name'] = None   # 鹿児島はジャンル情報なし

                # MEMO: エリア名はhtmlから取れなくもないが、Excelベースの表構造になっているので相当しんどい
                # 最後まで本気でこのWebページ形式で行く感じで、エリア名の需要がめちゃくちゃ高ければ、諦めて対応する…かも

                yield item
