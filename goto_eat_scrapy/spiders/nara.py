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
    start_urls = ["https://premium-gift.jp/files/140/document/1660/利用店舗一覧.xlsx"]

    CACHE_PATH = pathlib.Path(__file__).parent.parent.parent / ".scrapy" / settings.HTTPCACHE_DIR / name
    CACHE_PATH.mkdir(parents=True, exist_ok=True)

    def parse(self, response):
        tmp_xlsx = str(self.CACHE_PATH / "利用店舗一覧.xlsx")

        with open(tmp_xlsx, "wb") as f:
            f.write(response.body)
            self.logzero_logger.info(f"💾 saved xlsx: {response.request.url} > {tmp_xlsx}")

        df = pd.read_excel(tmp_xlsx, sheet_name="リスト", dtype=str).fillna({"電話番号": "", "URL": ""})
        for _, row in df.iterrows():
            item = ShopItem()
            item["area_name"] = row["エリア"].strip()
            item["shop_name"] = row["店舗名称"]  # MEMO: 店舗名に改行が入ってるものがある
            item["genre_name"] = row["カテゴリー"].strip()
            item["address"] = row["住所"].strip()
            item["tel"] = row["電話番号"]
            item["official_page"] = row["URL"]

            yield item
