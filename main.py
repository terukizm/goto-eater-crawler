import argparse
import pathlib

from logzero import logger
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from goto_eat_scrapy.scripts.hokkaido import HokkaidoCrawler
from goto_eat_scrapy.scripts.oita import crawl as oita_crawl


class Main:
    def __init__(self, base: pathlib.Path, target=None):
        self.csv_dir = base / "csvs"
        self.log_dir = base / "logs"
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        settings = get_project_settings()
        settings.set("LOG_LEVEL", "WARNING")
        settings.set("FEED_FORMAT", "csv")
        settings.set("FEED_URI", str(self.csv_dir / "%(name)s.csv"))
        self.settings = settings

    def run(self, target):
        targets = target.split(",") if target else None
        if not targets:  # all
            # 特定の都道府県を除いて一括実行
            ignores = [
                "tokyo_gnavi",  # 企業サイトであり、かつ件数が多く、詳細ページまで見る必要があり、アクセスが多くなってしまうため。東京都はPDF版クローラで対応。
                "tokushima",  # 「※本サイトのコンテンツの無断転載を禁じます。」という一文があるため (2020/12/09)
            ]
            process = CrawlerProcess(self.settings)
            targets = [x for x in process.spider_loader.list() if not x in ignores]
            targets += ["hokkaido", "oita"]

        if "hokkaido" in targets:
            self.run_hokkaido()
            targets.remove("hokkaido")
        if "oita" in targets:
            self.run_oita()
            targets.remove("oita")
        if targets:
            self.run_spiders(spiders=targets)

        logger.info("completed!! ")

    def run_spiders(self, spiders: list):
        logger.info("ScrapyのSpiderを実行 ... ")
        process = CrawlerProcess(self.settings)
        for spider in spiders:
            logger.info(f"[ {spider} ] start ...")

            # log, csvは上書き(ローテーションなし)
            # MEMO: 2020/10リリースのv2.4.0以降で追加されたoverwriteオプションでCSVを上書きできればよいのだが、
            # イマイチ使い方がわからないので、古いCSVを削除することで結果が追記されないようにしている
            csvfile = self.csv_dir / f"{spider}.csv"
            logfile = self.log_dir / f"{spider}.log"
            csvfile.unlink(missing_ok=True)
            logfile.unlink(missing_ok=True)

            process.crawl(spider, logfile=logfile)

        process.start()

    def run_hokkaido(self):
        # FIXME: multiprocessing.Processでやっつけ並行処理していたが、loggingがうまく出ない(loggerが差し替えられてしまう？)ので
        # ゴリゴリ書いている。北海道、大分県ともに多少件数はあるが、まあ処理しきれないほどの件数ではないので…
        target = "hokkaido"
        logger.info(f"[ {target} ] start ...")
        csvfile = self.csv_dir / f"{target}.csv"
        logfile = self.log_dir / f"{target}.log"
        csvfile.unlink(missing_ok=True)
        logfile.unlink(missing_ok=True)
        c1 = HokkaidoCrawler(csvfile, logfile)
        c1.crawl()
        logger.info(f"[ {target} ]  end  ...")

    def run_oita(self):
        target = "oita"
        logger.info(f"[ {target} ] start ...")
        csvfile = self.csv_dir / f"{target}.csv"
        logfile = self.log_dir / f"{target}.log"
        csvfile.unlink(missing_ok=True)
        logfile.unlink(missing_ok=True)
        oita_crawl(csvfile, logfile)
        logger.info(f"[ {target} ]  end  ...")


if __name__ == "__main__":
    # usage:
    # $ python main.py
    # $ python main.py --target tochigi,oita,gunma

    # TODO: まともにオプション引数をやる
    parser = argparse.ArgumentParser(description="goto-eat-crawler")
    parser.add_argument("--basedir", help="例: data")
    parser.add_argument("--target", help="例: tochigi,gunma")
    args = parser.parse_args()

    base = pathlib.Path(args.basedir) if args.basedir else pathlib.Path(__file__).parent / "data" / "input"
    runner = Main(base)
    runner.run(args.target)

    logger.info(f"👍 終了")
