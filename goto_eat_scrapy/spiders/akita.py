import pathlib

import pandas as pd

from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class AkitaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl akita -O akita.csv
    """

    name = "akita"
    allowed_domains = ["gotoeat-akita.com"]
    start_urls = ["https://gotoeat-akita.com/csv/list.csv"]

    def parse(self, response):
        # MEMO: tempfile, io.stringIO等ではpd.read_csv()がきちんと動作しなかったので
        # scrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)に書き込んでいる
        cache_dir = pathlib.Path(__file__).parent.parent.parent / ".scrapy" / settings.HTTPCACHE_DIR / self.name
        tmp_csv = str(cache_dir / "list.csv")
        with open(tmp_csv, "wb") as f:
            f.write(response.body)
        self.logzero_logger.info(f"💾 saved csv: {response.request.url} > {tmp_csv}")

        df = pd.read_csv(tmp_csv, header=None, names=("店舗名", "市町村", "所在地", "電話番号", "公式ホームページ")).fillna(
            {"公式ホームページ": "", "電話番号": ""}
        )

        for _, row in df.iterrows():
            item = ShopItem()

            # MEMO: 店舗名情報に <!-- --> 形式で検索用(?)のふりがな/フリガナが入っているが、
            # item pipelineでHTMLタグとして剥ぎ取られる
            item["shop_name"] = row["店舗名"]

            # 同じく検索用(?)の文字列が入っているものがあるが、こちらの入力値は利用する
            # (申請時に住所として未入力だった項目を手作業で埋めてる？)
            item["address"] = row["所在地"].replace("<!--", "").replace("-->", "").strip()

            item["area_name"] = row["市町村"]
            item["tel"] = row["電話番号"]
            item["official_page"] = row["公式ホームページ"]
            # item['genre_name'] = None    # 秋田県はジャンル情報なし

            yield item
