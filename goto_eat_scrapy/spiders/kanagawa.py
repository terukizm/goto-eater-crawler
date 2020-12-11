from goto_eat_scrapy.spiders.abstract_liny import AbstractLinySpider

class KanagawaSpider(AbstractLinySpider):
    """
    usage:
      $ scrapy crawl kanagawa -O kanagawa.csv
    """
    name = 'kanagawa'
    allowed_domains = [ 'gotoeat-kanagawa.liny.jp' ]
    base_url = 'https://gotoeat-kanagawa.liny.jp/map/api/data.json'

    x_min = 35.1
    x_max = 35.6
    y_min = 138.9
    y_max = 139.8
    step = 0.02
