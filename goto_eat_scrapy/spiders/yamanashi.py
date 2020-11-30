import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class YamanashiSpider(AbstractSpider):
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
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for section in response.xpath('//*[@id="shopList"]/section[@class="shopInfoSection"]'):
            area_name = section.xpath('.//h1/text()').get().strip()
            # テーブル中の各行をparse(先頭行はヘッダなので飛ばす)
            for tr in section.xpath('.//div[@class="secInnr"]/table[@class="shopTable"]/tr')[1:]:
                item = ShopItem(
                    area_name = area_name,
                    shop_name = tr.xpath('.//td[1]/text()').get().strip(),
                    genre_name = tr.xpath('.//td[1]/span[@class="genre"]/a/text()').get().strip(),
                    address = tr.xpath('.//td[2]/text()').get().strip(),
                    tel = tr.xpath('.//td[3]/text()').get().strip(),
                )
                self.logzero_logger.debug(item)
                yield item
