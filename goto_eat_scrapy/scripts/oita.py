import asyncio
from pyppeteer import launch
from pyppeteer.errors import PageError
import lxml.html
import pathlib
import pandas as pd
from logzero import logger
from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem

async def crawl():
    browser = await launch({
        'defaultViewport': None,
        'headless': True,           # pipenvなど手元で動かしている場合はFalseにすると実際にchroniumが動くのでわかりやすい
        'args': ['--no-sandbox'],   # Docker内で動かす場合に必要(あんまりよろしくないらしいが)
        'slowMo': 5,                # 適宜食わせないとコケる(？)ので
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

    if not html:
        raise Exception('html is none....')

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

def main(outfile: str):
    # クローリングは時間かかるので一回成功したらpickleにしてる
    # 保存先はscrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)
    # TODO: この辺のcache処理を消す、もしくはオプションにする
    cache_dir = pathlib.Path.cwd() / '.scrapy' / settings.HTTPCACHE_DIR / 'oita_script'
    cache_dir.mkdir(parents=True, exist_ok=True)
    _html_pkl = str(cache_dir / 'pyppeteer.pkl')
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
    df.to_csv(outfile, index=False, encoding=settings.FEED_EXPORT_ENCODING)


if __name__ == "__main__":
    """
    大分県のサイトはSPAなのでscrapy単体では処理できない。
    splashを大分のためだけに使うのもめんどくさかったので、pyppeteerでゴリゴリ実装。

    usage:
    $ python -m goto_eat_scrapy.scripts.oita
    """
    outfile = '/tmp/44_oita.csv'
    main(outfile)
    logger.info(f'👍 success!! > {outfile}')
