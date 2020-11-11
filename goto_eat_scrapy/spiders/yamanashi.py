import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.exceptions import ScrapingError

class YamanashiSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl yamanashi -O output.csv
    """
    name = 'yamanashi'
    allowed_domains = [ 'gotoeat-yamanashi.jp' ]

    # 山梨県はこの1ページだけでOK(ページングなし)
    start_urls = ['https://www.gotoeat-yamanashi.jp/archives/merchant']

    def parse(self, response):
        # 市区町村単位(甲府市〜小菅村)
        for section in response.xpath('//*[@id="shopList"]/section[@class="shopInfoSection"]'):
            # テーブル中の各行をparse(先頭はヘッダなので飛ばす)
            for tr in section.xpath('.//div[@class="secInnr"]/table[@class="shopTable"]/tr')[1:]:
                yield ShopItem(
                    shop_name = tr.xpath('.//td[1]/text()').get().strip(),
                    genre_name = tr.xpath('.//td[1]/span[@class="genre"]/a/text()').get().strip(),
                    address = tr.xpath('.//td[2]/text()').get().strip(),
                    tel = tr.xpath('.//td[3]/text()').get().strip(),
                )
