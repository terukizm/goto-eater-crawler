import re

import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class FukuiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl fukui -O fukui.csv
    """

    name = "fukui"
    allowed_domains = ["gotoeat-fukui.com"]

    # MEMO: 稀に503になるので、個別にDELAYを多めに設定して様子見
    # ただし福井はそもそも詳細ページまで回してて件数が多いので、あまり多くしすぎると時間がかかってしまう
    custom_settings = {
        "DOWNLOAD_DELAY": 4,
    }

    def start_requests(self):
        params = {"Keyword": "", "Action": "text_search"}
        yield scrapy.FormRequest(
            "https://gotoeat-fukui.com/shop/search.php", callback=self.search, method="POST", formdata=params
        )

    def search(self, response):
        # 福井県は検索結果のページングなし
        self.logzero_logger.info(f"💾 url(search) = {response.request.url}")
        for article in response.xpath('//div[@class="result"]/ul/li'):
            url = article.xpath(".//a/@href").get().strip()
            yield scrapy.Request(response.urljoin(url), callback=self.detail)

    def detail(self, response):
        self.logzero_logger.info(f"💾 url(detail) = {response.request.url}")
        item = ShopItem()
        item["shop_name"] = response.xpath('//div[@id="contents"]/h3/text()').get().strip()
        item["area_name"] = (
            response.xpath('//div[@id="contents"]/div[@class="icon"]/span[@class="area"]/text()').get().strip()
        )
        item["detail_page"] = response.request.url

        for dl in response.xpath('//div[@id="contents"]/dl'):
            # MEMO: ジャンル指定がされていない(dt[1]が空の)データ、「グルメ民宿 はまもと」があり、その場合following-siblingが変なところ
            # (dd/text()の値が存在する「住所」？)を見に行ってしまうので、暫定的にジャンル部分だけ直接指定で実装
            # 参考: https://gotoeat-fukui.com/shop/?id=180097  (にしても画像がうまそうでつらい)
            # 元データが修正されれば以下の実装でよい
            # genre_name = dl.xpath('.//dt[contains(text(), "ジャンル")]/following-sibling::dd/text()').get().strip()
            genre_name = dl.xpath(".//dd[1]/text()").get()
            genre_name = genre_name.strip() if genre_name else ""  # はまもとだけの例外対応
            item["genre_name"] = genre_name.replace("、", "|")  # 複数ジャンルあり

            item["tel"] = dl.xpath('.//dt[contains(text(), "電　　話")]/following-sibling::dd/a/text()').get().strip()
            item["address"] = dl.xpath('.//dt[contains(text(), "住　　所")]/following-sibling::dd/text()').get().strip()
            item["opening_hours"] = (
                dl.xpath('.//dt[contains(text(), "営業時間")]/following-sibling::dd/text()').get()
            )
            item["closing_day"] = dl.xpath('.//dt[contains(text(), "定 休 日")]/following-sibling::dd/text()').get()
            item["official_page"] = dl.xpath('.//dt[contains(text(), "HP・SNS")]/following-sibling::dd/text()').get()

            gmap_url = (
                dl.xpath('.//dt[contains(text(), "住　　所")]/following-sibling::dd/a[@class="gmap"]/@href').get().strip()
            )
            m = re.search("q=(?P<lat>\d+\.\d+)\,(?P<lng>\d+\.\d+)", gmap_url)
            if m:
                item["provided_lat"] = m.group("lat")
                item["provided_lng"] = m.group("lng")

        return item
