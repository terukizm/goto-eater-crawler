import json
import pathlib

import numpy as np
import scrapy

from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


def _get_max_and_min(coordinates: list):
    """
    GeoJSONのfeatures.geometry.coordinatesから、1kmメッシュに含まれるlatlngのmin/maxを求める
    (これがx1,x2,y1,y2の各値と対応)
    """
    for i, coords in enumerate(coordinates[0]):
        lat = coords[1]
        lng = coords[0]
        if i == 0:
            lat_min = lat
            lat_max = lat
            lng_min = lng
            lng_max = lng
            continue
        if lat < lat_min:
            lat_min = lat
        if lat_max < lat:
            lat_max = lat
        if lng < lng_min:
            lng_min = lng
        if lng_max < lng:
            lng_max = lng

    return (lat_min, lat_max, lng_min, lng_max)


class AbstractLinySpider(AbstractSpider):
    allowed_domains = ["liny.jp"]

    def start_requests(self):
        path = pathlib.Path(__file__).parent / "1km_mesh" / self.mesh_geojson_name
        with open(path) as f:
            geojson = json.load(f)
            for record in geojson["features"]:
                x1, x2, y1, y2 = _get_max_and_min(record["geometry"]["coordinates"])
                url = f"{self.base_url}?x1={x1}&x2={x2}&y1={y1}&y2={y2}"
                self.logzero_logger.info(f"💾 url = {url}")
                yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # json形式なので、response.body(bytes)を直接読める
        for article in json.loads(response.body)["data"]:
            item = ShopItem(
                shop_name=article["name"],
                address=article["address"],
                tel=article["tel"],
                official_page=article["url"],
                # MEMO: eigyo_jikan内に定休日も含まれているが基本的に自由書式のため、分別しようがない
                # まとめて全部、営業時間の方に入れておく
                opening_hours=article["eigyo_jikan"],
                # MEMO: liny系は公式にlatlng(google mapの結果とはまた別っぽい…？)が提供されているので、
                # これをジオコーディングせずにそのまま使えば精度が出せる
                provided_lat=article["latlng"]["lat"],
                provided_lng=article["latlng"]["lng"],
            )

            yield item


if __name__ == "__main__":
    # usage:
    # $ python -m goto_eat_scrapy.spiders.abstract_liny
    coordinates = [
        [
            [140.1125, 35.5416666666667],
            [140.125, 35.5416666666667],
            [140.125, 35.55],
            [140.1125, 35.55],
            [140.1125, 35.5416666666667],
        ]
    ]
    x1, x2, y1, y2 = _get_max_and_min(coordinates)
    assert x1 == 35.5416666666667
    assert x2 == 35.55
    assert y1 == 140.1125
    assert y2 == 140.125

    print("success!!")
