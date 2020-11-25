import requests
import lxml
import time
import pathlib
import pandas as pd
from logzero import logger
from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem

# Cookieを保持するため、本来はちゃんとクラスにしてあげたりするとよさげ(気力が…)
session = requests.Session()

CACHE_PATH = pathlib.Path.cwd() / '.scrapy' / settings.HTTPCACHE_DIR / 'hokkaido_script'
CACHE_PATH.mkdir(parents=True, exist_ok=True)

SLEEP_SEC = 3
HEADERS = {'User-Agent': settings.USER_AGENT}

def show_search_page():
    """
    「取扱店リスト」の初期表示(GET)
    """
    r = session.get('https://gotoeat-hokkaido.jp/general/particStores', headers=HEADERS)
    r.raise_for_status()     # retryなし。ステータスコード 40x/50x は例外で即終了とする

    html = lxml.html.fromstring(r.content)
    token = html.xpath('//p[@class="buttons"]/input[@name="_token"]/@value')[0]

    return token


def post_search(token, area):
    """
    エリアを選択して「検索する」ボタン押下(POST)
    """
    logger.info(f'POST ... (_token={token}, area={area})')
    params = {
        'store_area': area,
        'store_address1': '',
        'division1_id': '',
        'store_name': '',
        '_token': token,
    }

    time.sleep(SLEEP_SEC)
    r = session.post('https://gotoeat-hokkaido.jp/general/particStores/search', params, headers=HEADERS)
    r.raise_for_status()

    html = lxml.html.fromstring(r.content)
    return parse(html)


def get_page(url, area, with_cache=True):
    """
    検索結果をページング(GET /?page=xx)
    """
    logger.info(f'GET {url}...')

    # requestに対してのpickleを用いた簡易キャッシュ
    # 保存先はscrapyのhttpcacheと同じ場所(settings.HTTPCACHE_DIR)
    # TODO: この辺のcache処理を消す、もしくはオプションにする
    cache_file = CACHE_PATH / '{}_{}.pkl'.format(url.replace('/', '_').replace('?', '_'), area)
    if with_cache and cache_file.exists():
        logger.debug(f'  load from cache... {cache_file}')
        r = pd.read_pickle(cache_file)
    else:
        time.sleep(SLEEP_SEC)
        r = session.get(url, headers=HEADERS)
        r.raise_for_status()
        pd.to_pickle(r, cache_file)
        logger.debug(f'  write cache. {cache_file}')

    html = lxml.html.fromstring(r.content)
    return parse(html)


def parse(html):
    result = []
    for article in html.xpath('//div[@id="contents"]/div[@class="results"]/ul/li'):
        item = ShopItem()
        item['shop_name'] = article.xpath('.//div[@class="left"]/h4[@class="results-tit"]/text()')[0].strip()
        item['address'] = article.xpath('.//div[@class="left"]/p[@class="results-txt01"]/text()')[0].strip()
        item['genre_name'] = article.xpath('.//div[@class="right"]/p[@class="results-txt02"]/text()')[0].strip()
        tel = article.xpath('.//div[@class="right"]/p[@class="results-txt03"]/text()')
        item['tel'] = tel[0].strip() if tel else None

        result.append(item)

    next_page = html.xpath('//ul[@role="navigation"]/li/a[@rel="next"]/@href')
    return result, next_page

def main(outfile: str):
    token = show_search_page()
    results = []
    for area in ['道央', '道北', '道南', '道東']:
        # 1p目(POST)
        result, next_page = post_search(token, area)
        results += result
        # 2P以降(GET)
        while next_page:
            result, next_page = get_page(url=next_page[0], area=area)
            results += result

    df = pd.DataFrame(results, columns=settings.FEED_EXPORT_FIELDS)
    df.to_csv(outfile, index=False, encoding=settings.FEED_EXPORT_ENCODING)


if __name__ == "__main__":
    """
    北海道のサイトはセッションを共有しているため、検索結果のURLが一意にならず、並列にアクセスすると結果が混ざってしまう。
    色々と試行錯誤したがScrapyではシンプルに処理できなかったため、愚直にrequests + lxmlでゴリゴリと実装した…

    usage:
    $ python -m goto_eat_scrapy.scripts.hokkaido
    """
    outfile = '/tmp/01_hokkaido.csv'
    main(outfile)
    print(f'success!! > {outfile}')
