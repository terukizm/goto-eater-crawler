import scrapy
import logging
import logzero
from scrapy import signals

class AbstractSpider(scrapy.Spider):
    def __init__(self, logfile=None, *args, **kwargs):
        logger_name = f'logzero_logger_{self.name}'
        if logfile:
            ## main.py経由で実行される場合
            # scrapyの標準ログ出力とは別に、
            # self.logzero_logger.debug()以上をlogfileにファイル出力
            self.logzero_logger = logzero.setup_logger(
                name=logger_name,
                logfile=logfile,
                fileLoglevel=logging.DEBUG,
                disableStderrLogger=True
            )
        else:
            ## scrapyコマンド経由で実行される場合
            #   例: scrapy crawl sage -O saga.csv
            # scrapyのログ出力(標準出力)に加え、self.logzero_logger.info()以上を
            # 標準出力に出す
            self.logzero_logger = logzero.setup_logger(
                name=logger_name,
                level=logging.INFO
            )

    # MEMO: やっつけエラーハンドリング (注意: spiderの中でraise Exceptionしても届かない)
    # GitHub Actionでログに出したやつを find xargs grep とかで拾って、エラーがあったらコケさせるような想定
    # slack notifyとかでもよい
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider._errback_handle, signal=signals.spider_error)
        return spider

    def _errback_handle(self, failure, response, spider):
        # @see https://blog.mudatobunka.org/entry/2016/09/24/232456
        spider.logzero_logger.error(f'Spider Error ### {spider.name} ###')
        spider.logzero_logger.error('{} {}'.format(failure.type, failure.getErrorMessage()))
