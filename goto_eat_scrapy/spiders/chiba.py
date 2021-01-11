from goto_eat_scrapy.spiders.abstract_liny import AbstractLinySpider


class ChibaSpider(AbstractLinySpider):
    """
    usage:
      $ scrapy crawl chiba -O chiba.csv
    """

    name = "chiba"
    base_url = "https://gotoeat-chiba.liny.jp/map/api/data.json"
    mesh_geojson_name = "12chiba1km.geojson"

    # 千葉は広いせいか、途中でセッションが切れて(？) 502 Bad Gateway が出るケースがあるので…
    custom_settings = {
        "DOWNLOAD_DELAY": 1.25,
    }
