
import scrapy
import json
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class KochiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl kochi -O kochi.csv
    """
    name = 'kochi'
    allowed_domains = [ 'gotoeat-kochi.jp' ]

    start_urls = [
        'https://www.gotoeat-kochi.com/js/shop_list.php',   # jsonが帰ってくる
    ]

    def parse(self, response):
        # json形式なので、response.body(bytes)を直接読める
        for row in json.loads(response.body):
            # おそらく
            #   0: area_code,
            #   1: area_name,
            #   2: genre_code,
            #   3: genre_name,
            #   4: ???,
            #   5: shop_name,
            #   6: shop_name_kana,
            #   7: address,
            #   8: tel
            item = ShopItem(
                area_name = row[1],
                genre_name = row[3],
                shop_name = row[5],
                address = row[7],
                tel = row[8],
            )

            yield item
