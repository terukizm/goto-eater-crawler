import pathlib

import fitz
import pandas as pd
import scrapy
import tabula

from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class TokyoSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl tokyo -O output.csv
    """

    name = "tokyo"
    allowed_domains = ["gnavi.co.jp"]
    start_urls = ["https://r.gnavi.co.jp/plan/campaign/gotoeat-tokyo/"]

    CACHE_PATH = pathlib.Path(__file__).parent.parent.parent / ".scrapy" / settings.HTTPCACHE_DIR / name
    CACHE_PATH.mkdir(parents=True, exist_ok=True)

    def parse(self, response):
        for li in response.xpath('//section[@id="c-search__pdf"]/ul/li'):
            pdf_url = li.xpath(".//a/@href").get().strip()
            yield scrapy.Request(pdf_url, callback=self.parse_from_pdf)

    def parse_from_pdf(self, response):
        # MEMO: tempfile, io.stringIOではきちんと動作しなかったので、
        # scrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)に書き込んでいる
        prefix = (
            response.request.url.replace("https://pr.gnavi.co.jp/promo/gotoeat-tokyo/pdf/", "")
            .replace("/", "-")
            .replace(".pdf", "")
        )
        tmp_pdf = str(self.CACHE_PATH / f"{prefix}.pdf")
        with open(tmp_pdf, "wb") as f:
            f.write(response.body)
            self.logzero_logger.info(f"💾 saved pdf: {response.request.url} > {tmp_pdf}")

        # MEMO: pymupdfは比較的綺麗に取れるが、空セルを読み飛ばしてしまうため、空セルがありえるURL行が難しかった。
        # また、Excelシートのヘッダー、フッター文字列(ページ番号とかを含むやつ)との兼ね合いなのか、最終ページだけ
        # 順番が入れ替わったりといった固有の問題もあり、最終的にはtabulaで1ページずつ(補正しつつ)処理していく方式とした。
        # PDF読み込みライブラリは色々あるが、読み込むPDFによって向き不向きが非常に大きいため、一つずつ試していくしかない…

        page_count = fitz.open(tmp_pdf).pageCount
        for page_no in range(1, page_count + 1):
            # tabulaで1ページ単位でCSVに変換してからdfに読み込む
            tmp_csv = self.CACHE_PATH / f"{prefix}_p{page_no}.csv"
            if not tmp_csv.exists():
                tabula.convert_into(
                    tmp_pdf, str(tmp_csv), output_format="csv", pages=page_no, lattice=True, silent=True
                )
                self.logzero_logger.info(f"💾 saved csv: >>>>>> {tmp_csv}")

            try:
                # ページによっては空行、空列、不要カラムを含むため、それらを除去
                df = pd.read_csv(tmp_csv, dtype=str).dropna(how="all").dropna(how="all", axis=1).reset_index(drop=True)
                df.columns = ["紙", "電子", "飲食店名", "店舗住所", "店舗電話番号", "URL", "業態"]
                df = df.drop(["紙", "電子"], axis=1).fillna("")
            except ValueError:
                # 最終ページで行数が少ないなど、1ページ中に有効なURLが1件もない場合に空行とみなされて
                # 該当行のURL列が削除されてしまうため、暫定対応
                df.columns = ["紙", "電子", "飲食店名", "店舗住所", "店舗電話番号", "業態"]
                df = df.drop(["紙", "電子"], axis=1).fillna("")
                df["URL"] = ""
            except Exception:
                self.logzero_logger.error(f"❗ {page_no}")
                self.logzero_logger.error(f"❗ {df}")
                raise

            for _, row in df.iterrows():
                if row["飲食店名"] == "飲食店名":
                    # MEMO: 特定ページでヘッダ列がうまく処理できない(データレコードに含まれてしまう)ことがあるため
                    continue
                item = ShopItem()
                item["shop_name"] = row["飲食店名"]
                item["address"] = row["店舗住所"]
                item["genre_name"] = row["業態"]
                item["tel"] = row["店舗電話番号"]
                item["official_page"] = row["URL"]
                yield item
