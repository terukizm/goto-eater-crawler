import asyncio
import logging
import pathlib

import logzero
import lxml.html
import nest_asyncio
import pandas as pd
from pyppeteer import launch
from pyppeteer.errors import PageError

from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem

nest_asyncio.apply()


class OitaCrawler:
    """
    大分県のサイトはSPAなのでscrapy単体では処理できない。
    splashを大分のためだけに使うのもめんどくさかったので、pyppeteerでゴリゴリ実装。
    """

    name = "oita"

    LOG_LEVEL = logging.DEBUG
    SLEEP_SEC = 2
    HEADERS = {"User-Agent": settings.USER_AGENT}
    CACHE_PATH = pathlib.Path.cwd() / ".scrapy" / settings.HTTPCACHE_DIR / f"{name}_script"
    CACHE_PATH.mkdir(parents=True, exist_ok=True)

    def _check_pyppeteer(self):
        # @see https://rinoguchi.hatenablog.com/entry/2020/08/09/004925#pyppeteererrorsBrowserError-Browser-closed-unexpectedly
        # Docker内でpyppeteerが動かない場合があるので、その確認用
        import os

        from pyppeteer.launcher import Launcher

        cmd: str = " ".join(Launcher({"args": ["--no-sandbox"]}).cmd)
        print(f"cmd: {cmd}")
        os.system(cmd)

    def __init__(self, csvfile=None, logfile=None, with_cache=True):
        # self._check_pyppeteer()
        logger_name = f"logzero_logger_{self.name}"
        if logfile:
            # ログファイルに出す(標準出力には出さない)
            self.logzero_logger = logzero.setup_logger(
                name=logger_name, logfile=logfile, fileLoglevel=self.LOG_LEVEL, disableStderrLogger=False
            )
        else:
            # 標準出力に出すのみ
            self.logzero_logger = logzero.setup_logger(name=logger_name, level=self.LOG_LEVEL)

        self.csvfile = csvfile
        self.logfile = logfile
        self.with_cache = with_cache

    async def crawl_by_pyppeteer(self):
        browser = await launch(
            {
                "defaultViewport": None,
                "logLevel": logging.INFO,  # 未指定だとroot loggerと同じになるので
                "args": ["--no-sandbox"],  # Docker内で動かす場合に必要
                "slowMo": 5,  # 適宜waitを食わせないとコケる(？)ので
                "headless": True,  # 手元で動かしている場合はFalseにすると、実際にchroniumが動くのでわかりやすい
            }
        )
        page = await browser.newPage()
        await page.goto("https://oita-gotoeat.com/shop/")

        try:
            # 適当にwait入れつつ無限スクロールの「もっと見る」ボタンを連打
            while True:
                await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
                await page.waitFor(self.SLEEP_SEC * 1000)
                await page.click('input[class="more"]')
                self.logzero_logger.debug("  next page...")
        except PageError:
            # FIXME: クソ実装、次ページがなくなったらボタンクリックができず、PageErrorがraiseされるのでループを抜ける
            pass

        html: str = await page.content()
        await browser.close()

        if not html:
            raise Exception("html is Not Found...")

        return html

    def parse(self, html: str):
        """
        lxmlを使ってxpathベースでparse
        """
        results = []
        response = lxml.html.fromstring(html)

        for article in response.xpath('//ul[@class="shop-list cf"]/li[@class="box-sh cf"]'):
            item = ShopItem()
            item["area_name"] = article.xpath('.//div[@class="tag cf"]/p[@class="area"]/span/text()')[0].strip()
            genres = [g.strip() for g in article.xpath('.//div[@class="tag cf"]/p[@class="genre"]/span/text()')]
            item["genre_name"] = "|".join(genres)

            item["shop_name"] = article.xpath('.//p[@class="name"]/text()')[0].strip()
            item["address"] = article.xpath('.//div[@class="first"]/p[@class="add"]/text()')[0].strip()

            tel = article.xpath('.//div[@class="second"]/p[@class="s-call"]/span[@class="shoptel"]/a/text()')
            item["tel"] = tel[0].strip() if tel else None
            official_page = article.xpath('.//div[@class="first"]/p[@class="web"]/a/@href')
            item["official_page"] = official_page[0].strip() if official_page else None

            results.append(item)

        return results

    def crawl(self):
        # クローリングは時間かかるので(開発用には)一回成功したら取得したhtmlをpickleにしてキャッシュ
        # 保存先はscrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)
        cache_file = self.CACHE_PATH / "pyppeteer.pkl"
        if self.with_cache and cache_file.exists():
            self.logzero_logger.debug(f"📗 load from cache... {cache_file}")
            html = pd.read_pickle(cache_file)
        else:
            self.logzero_logger.info("  crawling ...")
            html = asyncio.get_event_loop().run_until_complete(self.crawl_by_pyppeteer())
            if self.with_cache:
                pd.to_pickle(html, cache_file)
                self.logzero_logger.debug(f"💾  write cache. {cache_file}")

        # html文字列を解析
        df = pd.DataFrame(self.parse(html), columns=settings.FEED_EXPORT_FIELDS)

        if self.csvfile:
            df.to_csv(self.csvfile, index=False, encoding=settings.FEED_EXPORT_ENCODING)
            self.logzero_logger.info(f"  write csv. {self.csvfile}")
        else:
            self.logzero_logger.info(df)

        if len(df) < 2:
            raise Exception("CSVが空です。多分DOM構造が変わってるのでXPathを確認してください。")


if __name__ == "__main__":
    """
    usage:
    $ python -m goto_eat_scrapy.scripts.oita
    """

    crawler = OitaCrawler()
    crawler.crawl()

    # crawler = OitaCrawler(csvfile=pathlib.Path('/tmp/oita.csv'), logfile=pathlib.Path('/tmp/oita.log'), with_cache=True)
    # crawler.crawl()

    print(f"success!!")
