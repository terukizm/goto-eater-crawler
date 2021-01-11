from goto_eat_scrapy.spiders.abstract_liny import AbstractLinySpider


class ShigaSpider(AbstractLinySpider):
    """
    usage:
      $ scrapy crawl shiga -O shiga.csv
    """

    name = "shiga"
    base_url = "https://gotoeat-shiga.liny.jp/map/api/data.json"
    mesh_geojson_name = "25shiga1km.geojson"

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
    }
