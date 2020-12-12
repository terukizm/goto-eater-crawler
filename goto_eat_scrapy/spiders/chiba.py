from goto_eat_scrapy.spiders.abstract_liny import AbstractLinySpider

class ChibaSpider(AbstractLinySpider):
    """
    usage:
      $ scrapy crawl chiba -O chiba.csv
    """
    name = 'chiba'
    base_url = 'https://gotoeat-chiba.liny.jp/map/api/data.json'
    mesh_geojson_name = '12chiba1km.geojson'

