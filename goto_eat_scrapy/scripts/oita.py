import asyncio
from pyppeteer import launch
from pyppeteer.errors import PageError
import lxml.html
import pathlib
import pandas as pd
import logging
import logzero
from logzero import logger
from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem

class OitaCrawler():
    name = 'oita'

    LOG_LEVEL = logging.DEBUG
    SLEEP_SEC = 3
    HEADERS = {'User-Agent': settings.USER_AGENT}
    CACHE_PATH = pathlib.Path.cwd() / '.scrapy' / settings.HTTPCACHE_DIR / f'{name}_script'

    def __init__(self, csvfile=None, logfile=None, with_cache=True):
        logger_name = f'logzero_logger_{self.name}'
        if logfile:
            # ログファイルに出す(標準出力には出さない)
            self.logzero_logger = logzero.setup_logger(
                name=logger_name,
                logfile=logfile,
                fileLoglevel=self.LOG_LEVEL,
                disableStderrLogger=True
            )
        else:
            # 標準出力に出すのみ
            self.logzero_logger = logzero.setup_logger(
                name=logger_name,
                level=self.LOG_LEVEL
            )

        self.csvfile = csvfile
        self.logfile = logfile
        self.with_cache = with_cache
        if with_cache:
            self.CACHE_PATH.mkdir(parents=True, exist_ok=True)


    async def crawl_by_pyppeteer(self):
        browser = await launch({
            'defaultViewport': None,
            'headless': True,           # 手元で動かしている場合はFalseにすると、実際にchroniumが動くのでわかりやすい
            'args': ['--no-sandbox'],   # Docker内で動かす場合に必要
            'slowMo': 5,                # 適宜waitを食わせないとコケる(？)ので
        })
        page = await browser.newPage()
        await page.goto('https://oita-gotoeat.com/shop/')

        try:
            # 適当にwait入れつつ無限スクロールの「もっと見る」ボタンを連打
            while True:
                await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
                await page.waitFor(self.SLEEP_SEC * 1000);
                await page.click('input[class="more"]')
                self.logzero_logger.debug('  next page...')
        except PageError:
            # FIXME: クソ実装、次ページがなくなったらボタンクリックができず、PageErrorがraiseされるのでループを抜ける
            pass

        html: str = await page.content()
        await browser.close()

        if not html:
            raise Exception('html is none....')

        return html


    def parse(self, html: str):
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

            self.logzero_logger.debug(item)
            results.append(item)

        return results


    def crawl(self):
        # クローリングは時間かかるので(開発用には)一回成功したら取得したhtmlをpickleにしてキャッシュ
        # 保存先はscrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)
        cache_file = self.CACHE_PATH / 'pyppeteer.pkl'
        if self.with_cache and cache_file.exists():
            self.logzero_logger.debug(f'  load from cache... {cache_file}')
            html = pd.read_pickle(cache_file)
        else:
            self.logzero_logger.info('  crawling ...')
            html = asyncio.get_event_loop().run_until_complete(self.crawl_by_pyppeteer())
            if self.with_cache:
                pd.to_pickle(html, cache_file)
                self.logzero_logger.debug(f'  write cache. {cache_file}')

        # html文字列を解析
        df = pd.DataFrame(self.parse(html), columns=settings.FEED_EXPORT_FIELDS)
        if self.csvfile:
            df.to_csv(self.csvfile, index=False, encoding=settings.FEED_EXPORT_ENCODING)
            self.logzero_logger.info(f'  write csv. {self.csvfile}')
        else:
            self.logzero_logger.info(df)


if __name__ == "__main__":
    """
    大分県のサイトはSPAなのでscrapy単体では処理できない。
    splashを大分のためだけに使うのもめんどくさかったので、pyppeteerでゴリゴリ実装。

    usage:
    $ python -m goto_eat_scrapy.scripts.oita
    """
    crawler = OitaCrawler()
    crawler.crawl()

    # crawler = OitaCrawler(csvfile=pathlib.Path('/tmp/oita.csv'), logfile=pathlib.Path('/tmp/oita.log'), with_cache=True)
    # crawler.crawl()

    print(f'success!!')
