import logging
import pathlib

import logzero
import lxml.html
import pandas as pd
from playwright.sync_api import sync_playwright

from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem

name = "oita"

CACHE_PATH = pathlib.Path.cwd() / ".scrapy" / settings.HTTPCACHE_DIR / f"{name}_script"
CACHE_PATH.mkdir(parents=True, exist_ok=True)


def run(playwright, logzero_logger):
    # iPhone11相当(webkit)でクローリングするが、UAは明示的にgoto-eaterを示す
    browser = playwright.webkit.launch(headless=True)
    device = playwright.devices["iPhone 11"]
    device["user_agent"] = settings.USER_AGENT
    context = browser.new_context(**device)

    page = context.new_page()
    page.goto("https://oita-gotoeat.com/shop/")

    try:
        # 無限スクロールの「もっと見る」ボタンを連打
        while True:
            page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
            page.click('input[class="more"]')
            logzero_logger.debug("next page...")
    except Exception:
        pass

    html = page.content()
    context.close()
    browser.close()

    if not html:
        raise Exception("html is Not Found...")

    return html


def parse(html: str):
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


def crawl(csvfile=None, logfile=None, with_cache=True):
    if logfile:
        # ログファイルへの出力
        logzero_logger = logzero.setup_logger(
            name=name,
            logfile=logfile,
            level=logging.INFO,
            fileLoglevel=logging.DEBUG,
            # formatter=None,
            disableStderrLogger=False,
        )
    else:
        # 標準出力(開発用)
        logzero_logger = logzero.setup_logger(name=name, level=logging.DEBUG, disableStderrLogger=False)

    # クローリングは時間かかるので(開発用には)一回成功したら取得したhtmlをpickleにしてキャッシュ
    # 保存先はscrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)
    cache_file = CACHE_PATH / "playwright.pkl"
    if with_cache and cache_file.exists():
        logzero_logger.debug(f"📗 load from cache... {cache_file}")
        html = pd.read_pickle(cache_file)
    else:
        logzero_logger.info("  crawling ...")
        with sync_playwright() as playwright:
            html = run(playwright, logzero_logger)
        if with_cache:
            pd.to_pickle(html, cache_file)
            logzero_logger.debug(f"💾  write cache. {cache_file}")

    # html文字列を解析
    df = pd.DataFrame(parse(html), columns=settings.FEED_EXPORT_FIELDS)

    if csvfile:
        df.to_csv(csvfile, index=False, encoding=settings.FEED_EXPORT_ENCODING)
        logzero_logger.info(f"  write csv. {csvfile}")
    else:
        logzero_logger.info(df)

    if len(df) < 2:
        raise Exception("CSVが空です。多分DOM構造が変わってるのでXPathを確認してください。")


if __name__ == "__main__":
    """
    usage:
    $ python -m goto_eat_scrapy.scripts.oita
    """

    crawl()

    print(f"success!!")
