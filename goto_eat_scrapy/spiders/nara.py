import pathlib

import pandas as pd
import scrapy

from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class naraSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl nara -O nara.csv
    """

    name = "nara"
    allowed_domains = ["premium-gift.jp"]

    # MEMO: 利用店舗一覧の中から適当にリンクが貼られている
    # @see https://premium-gift.jp/nara-eat/use_store
    start_urls = ["https://premium-gift.jp/nara-eat/use_store/detail?id=215783"]

    CACHE_PATH = pathlib.Path(__file__).parent.parent.parent / ".scrapy" / settings.HTTPCACHE_DIR / name
    CACHE_PATH.mkdir(parents=True, exist_ok=True)

    def parse(self, response):
        xlsx_url = response.xpath(
            '//table[@class="common-table"]/tbody/tr/th[contains(text(), "URL")]/following-sibling::td/a/@href'
        ).extract_first()
        yield scrapy.Request(xlsx_url, callback=self.parse_from_xlsx)

    def parse_from_xlsx(self, response):
        tmp_xlsx = str(self.CACHE_PATH / "利用店舗一覧.xlsx")

        with open(tmp_xlsx, "wb") as f:
            f.write(response.body)
            self.logzero_logger.info(f"💾 saved xlsx: {response.request.url} > {tmp_xlsx}")

        df = pd.read_excel(tmp_xlsx, sheet_name="リスト", dtype=str).fillna({"店舗_TEL": "", "店舗_URL": ""})
        for _, row in df.iterrows():
            item = ShopItem()
            item["area_name"] = row["エリア"].strip()
            item["shop_name"] = row["店舗_名称"]  # MEMO: 店舗名に改行が入ってるものがある
            item["genre_name"] = row["カテゴリー"].strip()
            item["address"] = row["店舗_住所"].strip()
            item["tel"] = row["店舗_TEL"]
            item["official_page"] = row["店舗_URL"]

            yield item
