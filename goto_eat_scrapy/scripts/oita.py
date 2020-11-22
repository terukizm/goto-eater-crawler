import asyncio
from pyppeteer import launch
from pyppeteer.errors import PageError
import lxml.html
import pandas as pd
from logzero import logger
from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem

async def crawl():
    browser = await launch({
        'defaultViewport': None,
        # 開発中は以下を有効にすると実際にブラウザが動くのでわかりやすい
        # 'headless': False,
        # 'slowMo': 5,
    })
    page = await browser.newPage()
    await page.goto('https://oita-gotoeat.com/shop/')

    try:
        # 適当にwait入れつつ無限スクロールの「もっと見る」ボタンを連打
        while True:
            await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
            await page.waitFor(1000);
            await page.click('input[class="more"]')
    except PageError:
        # FIXME: クソ実装、次ページがなくなったらボタンクリックができず、PageErrorがraiseされるのでループを抜ける
        pass

    html: str = await page.content()
    await browser.close()

    return html


def parse(html: str):
    """
    lxmlを使ってxpathベースでparse
    """
    results = []
    response = lxml.html.fromstring(html)
    for article in response.xpath('//li[@class="box-sh cf"]'):
        item = ShopItem()
        item['genre_name'] = article.xpath('.//div[@class="tag cf"]/p[@class="genre"]/span/text()')[0].strip()
        item['shop_name'] = article.xpath('.//p[@class="name"]/text()')[0].strip()
        item['address'] = article.xpath('.//div[@class="first"]/p[@class="add"]/text()')[0].strip()
        tel = article.xpath('.//div[@class="second"]/p[@class="s-call"]/span[@class="shoptel"]/a/text()')
        item['tel'] = tel[0].strip() if tel else None

        logger.debug(item)
        results.append(item)

    return results


if __name__ == "__main__":
    """
    大分県のサイトはSPAなのでscrapy単体だと処理できない。
    splashを大分のためだけに使うのもめんどくさかったのでpyppeteerでゴリゴリ実装。

    usage:
    $ python -m goto_eat_scrapy.scripts.oita
    """
    # クローリングは時間かかるので一回成功したらpickleにしてる
    _html_pkl = "/tmp/44_oita.pkl"
    try:
        logger.info('  load from pickle ...')
        html = pd.read_pickle(_html_pkl)
    except FileNotFoundError:
        logger.info('  crawling ...')
        html = asyncio.get_event_loop().run_until_complete(crawl())
        pd.to_pickle(html, _html_pkl)
        logger.info('  write to pickle.')

    # html文字列を解析してShopItemに
    results = parse(html)

    df = pd.DataFrame(results, columns=settings.FEED_EXPORT_FIELDS)
    outfile = '/tmp/44_oita.csv' # やる気がおわりだよ
    df.to_csv(outfile, index=False)

    logger.info(f'👍 success!! > {outfile}')
