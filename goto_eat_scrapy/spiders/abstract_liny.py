import scrapy
import json
import numpy as np
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class AbstractLinySpider(AbstractSpider):
    # 千葉、滋賀が面積広くて時間かかるので…
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
    }

    # MEMO: 公式サイトから上下左右の端となる店舗を選んで「地図を拡大」、その地点のx,yの値をメモ。
    # ざっくり最小値/最大値を丸めてクローリングの範囲とする。
    # (stepは0.01〜0.02としている。あまり粗いと(マーカーの密集地は間引かれてしまうため)
    #  取りこぼしがあり、あまり細かいとリクエスト回数が多くなって時間がかかる)

    ## 神奈川
    # 下端: x1=35.133&x2=35.135&y1=139.608&y2=139.615   (x_min = 35.1)
    # 上端: x1=35.636&x2=35.639&y1=139.520&y2=139.527   (x_max = 35.6)
    # 左端: x1=35.235&x2=35.238&y1=138.991&y2=138.997   (y_min = 138.9)
    # 右端: x1=35.537&x2=35.540&y1=139.747&y2=139.753   (y_max = 139.8)

    ## 滋賀
    # 下端(x_min): x1=34.850&x2=34.854&y1=136.045&y2=136.051   (x_min) = 34.8
    # 上端(x_max): x1=35.555&x2=35.559&y1=136.179&y2=136.186   (x_max = 35.6)
    # 左端(y_min): x1=34.989&x2=34.994&y1=135.825&y2=135.831   (y_min) = 135.7
    # 右端(y_max): x1=35.342&x2=35.347&y1=136.405&y2=136.412   (y_max) = 136.5

    ## 千葉
    # 下端:       x1=34.900&x2=34.905&y1=139.884&y2=139.891   (x_min = 34.85)
    # 上端(左端):  x1=36.079&x2=36.080&y1=139.792&y2=139.793   (x_max = 36.1, y_min = 139.6)
    # 右端:       x1=35.727&x2=35.731&y1=140.864&y2=140.870   (y_max) =  140.9

    def start_requests(self):
        x_min = self.x_min
        x_max = self.x_max
        y_min = self.y_min
        y_max = self.y_max
        step = self.step
        for x1 in np.arange(x_min, x_max, step):
            for y1 in np.arange(y_min, y_max, step):
                x2 = x1 + step
                y2 = y1 + step
                yield scrapy.Request(f'{self.base_url}?x1={x1}&x2={x2}&y1={y1}&y2={y2}', callback=self.parse)

    def parse(self, response):
        # json形式なので、response.body(bytes)を直接読める
        for article in json.loads(response.body)['data']:
            item = ShopItem(
                shop_name = article['name'],
                address = article['address'],
                tel = article['tel'],
                official_page = article['url'],

                # MEMO: eigyo_jikan内に定休日も含まれているが基本的に自由書式のため、分別しようがない
                opening_hours = article['eigyo_jikan'],

                # TODO: liny系は公式にlatlng(google mapの結果とはまた別っぽい…？)が提供されているので、
                # これをジオコーディングせずにそのまま使えば精度が出せる
                # lat = article['latlng']['lat'],
                # lng = article['latlng']['lng'],
            )
            self.logzero_logger.debug(item)
            yield item
