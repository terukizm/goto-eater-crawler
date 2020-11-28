from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
import pathlib
import pandas as pd
import multiprocessing
from goto_eat_scrapy.scripts import oita
from goto_eat_scrapy.scripts import hokkaido
from logzero import logger
import datetime

def run_spiders(base='result/csv'):
    logger.info('... ScrapyのSpiderを実行 ... ')
    settings = get_project_settings()
    settings.set('FEED_URI', f'{base}/%(name)s.csv')
    settings.set('FEED_FORMAT', 'csv')
    settings.set('LOG_FILE', 'tmp/scrapy.log')  # scrapyのログ出力(request/httpcache周りの切り分け用)

    process = CrawlerProcess(settings)
    spiders = process.spiders.list()
    # 単体動作確認
    spiders = [
        # 'aichi',
        # 'aomori',
        # 'akita',
        # 'fukui',
        # 'fukuoka',
        # 'fukushima',
        # 'gifu',
        # 'gunma',
        # 'hiroshima',
        # 'hyogo',
        # 'ibaraki',
        # 'ishikawa',
        # 'iwate',
        # 'kagawa',
        # 'kagoshima',
        # 'kochi',
        # 'kumamoto',
        # 'kyoto',
        # 'mie',
        # 'miyazaki',
        # 'nagano',
        # 'nagasaki',
        # 'nara',
        # 'niigata',
        'okinawa',
        'osaka',
        # 'saga',
        # 'saitama',
        # 'shimane',
        # 'shizuoka',
        # 'tochigi',
        '',
        '',
        '',
        '',
    ]

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    for spider in spiders:
        # MEMO: 2020/10リリースのv2.4.0で追加されたoverwriteオプションでCSVを上書きできればよいのだが、
        # イマイチ使い方がわからないので古いCSVに追記されないように消している
        logger.info(f'[ {spider} ] start ...')
        (pathlib.Path.cwd() / f'{base}/{spider}.csv' ).unlink(missing_ok=True)
        process.crawl(spider, logfile=f'{base}/logs/{spider}_{timestamp}.log')
        logger.info(f'[ {spider} ]  end ...')

    process.start()
    logger.info('all complete!!! ')


def run_scripts(base='result/csv'):
    logger.info('... Scrapy以外で書かれたクローラを実行 ... ')
    p1 = multiprocessing.Process(name="北海道", target=hokkaido.main, args=(f'{base}/hokkaido.csv', ))
    p2 = multiprocessing.Process(name="大分県", target=oita.main, args=(f'{base}/oita.csv', ))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    logger.info('... 完了!!')


def sort_csv(base='result/csv'):
    logger.info('... 出力されたCSVをソート... ')
    target = pathlib.Path.cwd() / base
    for csv in list(target.glob('*.csv')):
        df = pd.read_csv(csv).sort_values(['shop_name', 'address', 'genre_name'])
        df.to_csv(csv, index=False) # 上書き
        # df.to_csv(csv.parent / (csv.name + '.csv.sorted'), index=False)  # 別名保存
    logger.info('... 完了!!')


if __name__ == "__main__":
    # TODO: use args
    run_spiders()
    # run_scripts()
    # sort_csv()

    logger.info('👍 完了')
