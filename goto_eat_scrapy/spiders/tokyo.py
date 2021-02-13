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
        ## MEMO: 東京のshop4.pdfは特によくコケるのでデバッグ用に
        # yield scrapy.Request('https://pr.gnavi.co.jp/promo/gotoeat-tokyo/pdf/shop4.pdf', callback=self.parse_from_pdf)
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

        # MEMO: pymupdfは比較的綺麗に取れるが、空セルを読み飛ばしてしまうため、空セルがありえるURLの対応行が難しかった。
        # また、Excelシートのヘッダー、フッター文字列(ページ番号とかを含むやつ)との兼ね合いなのか、最終ページだけ
        # 順番が入れ替わったりといった固有の問題もあり、最終的にはtabulaで1ページずつ(補正しつつ)処理していく方式とした。
        # PDF読み込みライブラリは色々あるが、読み込むPDFのデザインによって向き不向きが非常に大きいため、一つずつ試していくしかない…
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

                # MEMO: tabulaで1ページずつpdf2csv処理すると(概ね)きれいに取れるが、罫線とか罫線内のデータとかの関係で
                # 一部レイアウトがうまく取れない場合がある。そういった場合にdfを整形する処理
                # (本当は生成されたcsv自体をparseしてクレンジングしてからdfに読ませる方がよいが、もうpdfこねくり回すの辛いんすよ…)

                # CSVの最初の行が空白行で、ヘッダになってない場合がある
                if len(df.columns) == 7 and not "飲食店名" in df.columns:
                    # カラム名を強引に設定し、紛れ込んでいるヘッダ行を削除
                    df.columns = ["紙", "電子", "飲食店名", "店舗住所", "店舗電話番号", "URL", "業態"]
                    df = df[df.query("店舗住所 == '店舗住所' & 飲食店名 == '飲食店名'") != -1]
                # URL列が全部空になってるときがある(URLが存在しなくなってしまうので補填)
                if not "URL" in df.columns:
                    df["URL"] = ""

                df = df[["飲食店名", "店舗住所", "店舗電話番号", "URL", "業態"]].fillna("")
            except Exception as e:
                self.logzero_logger.error(e)
                self.logzero_logger.error(f"❗ {tmp_csv}")
                self.logzero_logger.error(f"❗ {df}")
                raise

            for _, row in df.iterrows():
                if row["飲食店名"] == "飲食店名":
                    # MEMO: 特定ページでヘッダ列がうまく処理できない(データレコードに含まれてしまう)ことがあるため
                    continue
                if not row["飲食店名"] or not row["店舗住所"]:
                    # MEMO: 不要カラムなどは削除してあるはずだが、PDFに空行が紛れ込んでいるため
                    continue

                item = ShopItem()
                item["shop_name"] = row["飲食店名"]
                item["address"] = row["店舗住所"]
                item["genre_name"] = row["業態"]
                item["tel"] = row["店舗電話番号"]
                item["official_page"] = row["URL"]
                yield item
