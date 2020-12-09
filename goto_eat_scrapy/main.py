from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
import pathlib
import pandas as pd
import argparse
from logzero import logger
from goto_eat_scrapy.scripts.oita import OitaCrawler
from goto_eat_scrapy.scripts.hokkaido import HokkaidoCrawler

class Main():
    def __init__(self, base: pathlib.Path, target=None):
        self.csv_dir = base / 'csvs'
        self.log_dir = base / 'logs'
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        settings = get_project_settings()
        settings.set('FEED_FORMAT', 'csv')
        settings.set('FEED_URI', str(self.csv_dir / '%(name)s.csv'))  # @see https://docs.scrapy.org/en/latest/topics/feed-exports.html#storage-uri-parameters
        settings.set('LOG_FILE', str(self.log_dir / '_scrapy.log'))   # scrapyのログ(request/httpcache周りの切り分け用)
        self.settings = settings

    def run(self, target):
        targets = target.split(',') if target else None
        if not targets:  # all
            # 特定の都道府県を除いて一括実行
            ignores = [
                'tokyo',     # 企業サイトであり、かつ件数が多く、詳細ページまで見る必要があり、アクセスが多くなってしまうため
                'tokushima', # 「※本サイトのコンテンツの無断転載を禁じます。」という一文があるため (2020/12/09)
                ### 以下は公式で地図アプリが提供されており、latlng自体がgoogle mapsから取ってきている値の可能性があるため
                'chiba',
                'kanagawa',
                'shiga',
            ]
            process = CrawlerProcess(self.settings)
            targets = [ x for x in process.spiders.list() if not x in ignores ]
            targets += ['hokkaido', 'oita']

        if 'hokkaido' in targets:
            self.run_hokkaido()
            targets.remove('hokkaido')
        if 'oita' in targets:
            self.run_oita()
            targets.remove('oita')
        if targets:
            self.run_spiders(spiders=targets)

        logger.info('completed!! ')

    def run_spiders(self, spiders: list):
        logger.info('ScrapyのSpiderを実行 ... ')
        process = CrawlerProcess(self.settings)
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

    def run_hokkaido(self):
        # FIXME: multiprocessing.Processでやっつけ並行処理していたが、loggingがうまく出ない(loggerが差し替えられてしまう？)ので
        # ゴリゴリ書いている。北海道、大分県ともに多少件数はあるが、まあ処理しきれないほどの件数ではないので…
        target = 'hokkaido'
        logger.info(f'[ {target} ] start ...')
        csvfile = self.csv_dir / f'{target}.csv'
        logfile = self.log_dir / f'{target}.log'
        csvfile.unlink(missing_ok=True)
        logfile.unlink(missing_ok=True)
        c1 = HokkaidoCrawler(csvfile, logfile)
        c1.crawl()
        logger.info(f'[ {target} ]  end  ...')

    def run_oita(self):
        # TODO: 北海道・大分県のリファクタリング
        target = 'oita'
        logger.info(f'[ {target} ] start ...')
        csvfile = self.csv_dir / f'{target}.csv'
        logfile = self.log_dir / f'{target}.log'
        csvfile.unlink(missing_ok=True)
        logfile.unlink(missing_ok=True)
        c2 = OitaCrawler(csvfile, logfile)
        c2.crawl()
        logger.info(f'[ {target} ]  end  ...')

    def sort_csv(self):
        logger.info('出力されたCSVをソート...')
        for csv in list(self.csv_dir.glob('*.csv')):
            # 出力されたCSVを店舗名、住所、(+ジャンル名)でソートした後、上書き
            df = pd.read_csv(csv).sort_values(['shop_name', 'address', 'genre_name'])
            df.to_csv(csv, index=False)
            # df.to_csv(csv.parent / (csv.name + '.csv.sorted'), index=False)  # 別名保存する場合
        logger.info('... 完了')


if __name__ == "__main__":
    # usage:
    # $ python -m goto_eat_scrapy.main
    # $ python -m goto_eat_scrapy.main --target tochigi,oita,gunma

    # TODO: まともにオプション引数をやる
    parser = argparse.ArgumentParser(description='goto-eat-crawler')
    parser.add_argument('--basedir', help='例: data')
    parser.add_argument('--target', help='例: tochigi,gunma')
    args = parser.parse_args()

    base = pathlib.Path(args.basedir) if args.basedir else pathlib.Path.cwd() / 'data'
    main = Main(base)
    main.run(args.target)
    main.sort_csv()

    logger.info(f'👍 終了')
