import requests
import lxml
import time
import pathlib
import pandas as pd
import logging
import logzero
from logzero import logger
from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem

class HokkaidoCrawler():
    name = 'hokkaido'

    LOG_LEVEL = logging.INFO
    SLEEP_SEC = 2
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
        self.session = requests.Session()
        self.token = self._show_search_page_and_get_token()
        self.with_cache = with_cache
        if with_cache:
            self.CACHE_PATH.mkdir(parents=True, exist_ok=True)


    def _show_search_page_and_get_token(self):
        """
        「取扱店リスト」の初期表示(GET)を行い、token(csrf対策用？)を取得
        """
        r = self.session.get('https://gotoeat-hokkaido.jp/general/particStores', headers=self.HEADERS)
        r.raise_for_status()     # リトライなし。ステータスコード 40x/50x は例外で即終了とする

        html = lxml.html.fromstring(r.content)
        token = html.xpath('//p[@class="buttons"]/input[@name="_token"]/@value')[0]

        return token


    def post_search(self, area):
        """
        エリアを選択して「検索する」ボタン押下(POST)
        """
        token = self.token
        self.logzero_logger.info(f'POST ... (_token={token}, area={area})')
        params = {
            'store_area': area,
            'store_address1': '',
            'division1_id': '',
            'store_name': '',
            '_token': token,
        }

        # FIXME: 本来はこっちもキャッシュするべきなんだけど手を抜いている
        time.sleep(self.SLEEP_SEC)
        r = self.session.post('https://gotoeat-hokkaido.jp/general/particStores/search', params, headers=self.HEADERS)
        r.raise_for_status()

        html = lxml.html.fromstring(r.content)
        return self.parse(html)


    def get_page(self, url, area):
        """
        検索結果をページング(GET /?page=xx)
        """
        self.logzero_logger.info(f'GET {url}...')

        # requestに対してのpickleを用いた簡易キャッシュ
        # 保存先はscrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)
        cache_file = self.CACHE_PATH / '{}_{}.pkl'.format(url.replace('/', '_').replace('?', '_'), area)
        if self.with_cache and cache_file.exists():
            self.logzero_logger.debug(f'  load from cache... {cache_file}')
            r = pd.read_pickle(cache_file)
        else:
            time.sleep(self.SLEEP_SEC)
            r = self.session.get(url, headers=self.HEADERS)
            r.raise_for_status()
            if self.with_cache:
                pd.to_pickle(r, cache_file)
                self.logzero_logger.debug(f'  write cache. {cache_file}')

        response = lxml.html.fromstring(r.content)
        return self.parse(response)


    def parse(self, response):
        """
        htmlを解析
        """
        result = []
        for article in response.xpath('//div[@id="contents"]/div[@class="results"]/ul/li'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//div[@class="left"]/h4[@class="results-tit"]/text()')[0].strip()
            item['address'] = article.xpath('.//div[@class="left"]/p[@class="results-txt01"]/text()')[0].strip()
            item['genre_name'] = article.xpath('.//div[@class="right"]/p[@class="results-txt02"]/text()')[0].strip()
            tel = article.xpath('.//div[@class="right"]/p[@class="results-txt03"]/text()')
            item['tel'] = tel[0].strip() if tel else None

            self.logzero_logger.debug(item)
            result.append(item)

        next_page = response.xpath('//ul[@role="navigation"]/li/a[@rel="next"]/@href')
        return result, next_page


    def crawl(self):
        results = []
        for area in ['道央', '道北', '道南', '道東']:
            # 検索結果の1P目(POST)
            result, next_page = self.post_search(area)
            results += result
            # 検索結果の2P以降(GET)
            while next_page:
                result, next_page = self.get_page(url=next_page[0], area=area)
                results += result

        df = pd.DataFrame(results, columns=settings.FEED_EXPORT_FIELDS)
        if self.csvfile:
            df.to_csv(self.csvfile, index=False, encoding=settings.FEED_EXPORT_ENCODING)
            self.logzero_logger.info(f'  write csv. {self.csvfile}')
        else:
            self.logzero_logger.info(df)


if __name__ == "__main__":
    """
    北海道のサイトはセッションを共有しているため、検索結果のURLが一意にならず、並列にアクセスすると結果が混ざってしまう。
    色々と試行錯誤したがScrapyではシンプルに処理できなかったため、愚直にrequests + lxmlでゴリゴリと実装した…

    usage:
    $ python -m goto_eat_scrapy.scripts.hokkaido
    """
    crawler = HokkaidoCrawler()
    crawler.crawl()

    # crawler = HokkaidoCrawler(csvfile=pathlib.Path('/tmp/hokkaido.csv'), logfile=pathlib.Path('/tmp/hokkaido.log'), with_cache=True)
    # crawler.crawl()

    print(f'success!!')
