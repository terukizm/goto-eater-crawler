from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
import pathlib
import pandas as pd
import multiprocessing
from logzero import logger
from goto_eat_scrapy.scripts.oita import OitaCrawler
from goto_eat_scrapy.scripts.hokkaido import HokkaidoCrawler

class Main():
    def __init__(self, base: pathlib.Path):
        self.csv_dir = base / 'csvs'
        self.log_dir = base / 'logs'
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def run_spiders(self):
        logger.info('ScrapyのSpiderを実行 ... ')
        settings = get_project_settings()
        settings.set('FEED_FORMAT', 'csv')
        settings.set('FEED_URI', str(self.csv_dir / '%(name)s.csv'))  # @see https://docs.scrapy.org/en/latest/topics/feed-exports.html#storage-uri-parameters
        settings.set('LOG_FILE', str(self.log_dir / '_scrapy.log'))   # scrapyのログ(request/httpcache周りの切り分け用)

        process = CrawlerProcess(settings)
        spiders = process.spiders.list()
        # 単体動作確認用
        spiders = [
            # 'aichi',
            # 'aomori',
            # 'akita',
            # 'ehime',
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
            'kagoshima',
            # 'kochi',
            # 'kumamoto',
            # 'kyoto',
            # 'mie',
            # 'miyagi',
            # 'miyazaki',
            # 'nagano',
            # 'nagasaki',
            # 'nara',
            # 'niigata',
            # 'okayama',
            # 'okinawa',
            # 'osaka',
            # 'saga',
            # 'saitama',
            # 'shimane',
            # 'shizuoka',
            # 'tochigi',
            # 'tokushima',  ### 「※本サイトのコンテンツの無断転載を禁じます。」という一文があるのでskip
            # 'tokyo',      ### 企業サイト(ぐ○なび)な上、件数が多くて、かつ詳細ページまで見ないといけない
            # 'tottori',
            # 'toyama',
            # 'wakayama',
            # 'yamagata',
            # 'yamaguchi',
            # 'yamanashi',
            #
            # MEMO: 未対応
            ### 公式で地図アプリが提供されており、latlng自体がgoogle mapsから取ってきてる値の可能性があるため
            # 'chiba',
            # 'kanagawa',
            # 'shiga'
        ]

        for spider in spiders:
            logger.info(f'[ {spider} ] start ...')

            # log, csvは上書き(ローテーションなし)
            # MEMO: 2020/10リリースのv2.4.0以降で追加されたoverwriteオプションでCSVを上書きできればよいのだが、
            # イマイチ使い方がわからないので、古いCSVを削除することで結果が追記されないようにしている
            csvfile = self.csv_dir / f'{spider}.csv'
            logfile = self.log_dir / f'{spider}.log'
            csvfile.unlink(missing_ok=True)
            logfile.unlink(missing_ok=True)

            process.crawl(spider, logfile=logfile)
            logger.info(f'[ {spider} ]  end  ...')

        process.start()
        logger.info('all complete!!! ')


    def run_scripts(self):
        logger.info('Scrapy以外で書かれたクローラを実行...')

        # FIXME: multiprocessing.Processでやっつけ並行処理していたが、loggingがうまく出ない(loggerが差し替えられてしまう？)ので
        # ゴリゴリ書いている。北海道、大分県ともに多少件数はあるが、まあ処理しきれないほどの件数ではないので…
        csvfile = self.csv_dir / 'hokkaido.csv'
        logfile = self.log_dir / 'hokkaido.log'
        csvfile.unlink(missing_ok=True)
        logfile.unlink(missing_ok=True)
        c1 = HokkaidoCrawler(csvfile, logfile)
        c1.crawl()

        # TODO: 北海道・大分県のリファクタリング
        csvfile = self.csv_dir / 'oita.csv'
        logfile = self.log_dir / 'oita.log'
        csvfile.unlink(missing_ok=True)
        logfile.unlink(missing_ok=True)
        c2 = OitaCrawler(csvfile, logfile)
        c2.crawl()

        logger.info('... 完了')


    def sort_csv(self):
        logger.info('出力されたCSVをソート...')
        for csv in list(self.csv_dir.glob('*.csv')):
            # 出力されたCSVを店舗名、住所、(ジャンル名)でソートした後、上書き
            df = pd.read_csv(csv).sort_values(['shop_name', 'address', 'genre_name'])
            df.to_csv(csv, index=False)
            # df.to_csv(csv.parent / (csv.name + '.csv.sorted'), index=False)  # 別名保存する場合
        logger.info('... 完了')


if __name__ == "__main__":
    # usage:
    # $ python -m goto_eat_scrapy.main

    # TODO: get from args
    base = pathlib.Path.cwd() / 'data'

    main = Main(base)
    main.run_scripts()
    # main.run_spiders()
    main.sort_csv()

    logger.info(f'👍 終了')
