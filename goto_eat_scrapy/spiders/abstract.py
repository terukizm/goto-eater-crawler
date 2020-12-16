import scrapy
import logging
import logzero

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

    # MEMO: きちんとやる場合エラーハンドリングを実装
    #   @see https://nori-life.com/get-error-download-scrapy/
