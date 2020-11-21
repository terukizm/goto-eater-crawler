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
CACHE_PATH.mkdir(parents=False, exist_ok=True)

SLEEP_SEC = 3
HEADERS = {'User-Agent': settings.USER_AGENT}

def show_search_page():
    """
    「取扱店リスト」の初期表示(GET)
    """
    r = session.get('https://gotoeat-hokkaido.jp/general/particStores', headers=HEADERS)
    r.raise_for_status()     # retryなし、40x / 50x は例外で即終了とする

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
        item['genre_name'] = _genre(article.xpath('.//div[@class="right"]/p[@class="results-txt02"]/text()')[0].strip())
        tel = article.xpath('.//div[@class="right"]/p[@class="results-txt03"]/text()')
        item['tel'] = tel[0].strip() if tel else None

        result.append(item)

    next_page = html.xpath('//ul[@role="navigation"]/li/a[@rel="next"]/@href')
    return result, next_page


def _genre(genre_name: str):
    # ジャンル名がめちゃめちゃになっているので、ある程度寄せる
    # TODO: csv2geojson側でやるべきかもしれない
    if genre_name in ['すし', '回転すし']:
        return 'すし'
    if genre_name in ['焼肉', 'ホルモン焼', 'ステーキ・鉄板焼', 'ジンギスカン']:
        return '焼肉・ステーキ・鉄板焼'
    if genre_name in ['日本料理・郷土料理', '懐石・割烹', '天ぷら・うなぎ', 'とんかつ', \
        'すきやき・しゃぶしゃぶ', 'かに料理・海鮮料理', 'おにぎり・釜飯', 'もつ焼・おでん', \
        '丼・鍋', 'その他の日本料理']:
        return '和食'
    if genre_name in ['フランス料理・イタリア料理', 'その他の西洋料理']:
        return '洋食'
    if genre_name in ['中華料理・台湾料理', 'ぎょうざ']:
        return '中華'
    if genre_name in ['ラーメン・中華そば', 'そば・うどん', 'スパゲティ・パスタ']:
        return '麺類'
    if genre_name in ['アジア・エスニック料理', '韓国料理', '無国籍料理・多国籍料理', 'インド料理・カレー']:
        return 'アジア・エスニック・多国籍料理'
    if genre_name in ['居酒屋・大衆酒場', 'ダイニングバー', 'ビヤホール・ビアレストラン'] \
        or genre_name.startswith('ショットバー') \
        or genre_name.startswith('スナック'):
        return '居酒屋・バー'
    if genre_name in ['カフェ・フルーツパーラー', '喫茶店・珈琲店・紅茶店・茶房', 'ベーカリーカフェ']:
        return 'カフェ・喫茶店'

    # この辺からカテゴライズなんもわからん…
    if genre_name in ['焼鳥', 'フライドチキン', 'から揚げ・ザンギ']:
        return '焼鳥・フライドチキン・から揚げ・ザンギ'
    if genre_name in ['ハンバーガー', '一般食堂・定食'] \
        or genre_name.startswith('バイキング') \
        or genre_name.startswith('レストラン'):
        return 'レストラン・ファーストフード・バイキング・食堂'
    if genre_name.startswith('イートイン'):
        return 'イートイン'
    if genre_name in ['その他', 'お好み焼き・焼きそば', 'たこ焼き・もんじゃ焼き']:
        return 'その他'

    # それ以外はその他に全部寄せても良いが、一応例外投げて停止するようにした
    # (しれっと新ジャンル追加されて落ちそう...)
    logger.error(f'unknown: {genre_name}')
    raise Exception('不明なジャンル')


if __name__ == "__main__":
    """
    北海道のサイトはセッションを共有しているため、検索結果のURLが一意にならず、また並列にアクセスすると結果が混ざってしまうので、
    色々試行錯誤したがScrapyでうまく処理できなかったため、愚直にrequests + lxmlでゴリゴリと実装した…

    usage:
    $ python -m goto_eat_scrapy.scripts.hokkaido
    """
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
    outfile = '/tmp/01_hokkaido.csv' # やる気がおわりだよ
    df.to_csv(outfile, index=False)

    print(f'success!! > {outfile}')
