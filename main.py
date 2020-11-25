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
    # scrapconfigure_logging(install_root_handler = False)
    # configure_logging({
    #     'LOG_LEVEL': 'DEBUG',
    # })
    settings = get_project_settings()
    settings.set('FEED_URI', f'{base}/%(name)s.csv')
    settings.set('LOG_FILE', 'tmp/scrapy.log')
    settings.set('LOG_LEVEL', 'DEBUG')
    process = CrawlerProcess(settings)

    spiders = process.spiders.list()
    spiders = [
        # 'nara',
        'saga',
    ]

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    for spider in spiders:
        print(f'[{spider}] start ...')
        process.crawl(spider, logfile=f'{base}/logs/{spider}_{timestamp}.log')
        print(f'[{spider}]  end ...')

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
    run_spiders()
    # run_scripts()
    # sort_csv()

    logger.info('👍 完了')
