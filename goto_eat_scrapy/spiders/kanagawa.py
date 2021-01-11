from goto_eat_scrapy.spiders.abstract_liny import AbstractLinySpider


class KanagawaSpider(AbstractLinySpider):
    """
    usage:
      $ scrapy crawl kanagawa -O kanagawa.csv
    """

    name = "kanagawa"
    base_url = "https://gotoeat-kanagawa.liny.jp/map/api/data.json"
    mesh_geojson_name = "14kanagawa1km.geojson"

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
    }
