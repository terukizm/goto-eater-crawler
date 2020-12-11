from goto_eat_scrapy.spiders.abstract_liny import AbstractLinySpider

class ChibaSpider(AbstractLinySpider):
    """
    usage:
      $ scrapy crawl chiba -O chiba.csv
    """
    name = 'chiba'
    allowed_domains = [ 'gotoeat-chiba.liny.jp' ]
    base_url = 'https://gotoeat-chiba.liny.jp/map/api/data.json'

    x_min = 34.85
    x_max = 36.1
    y_min = 139.6
    y_max = 140.9
    step = 0.02

