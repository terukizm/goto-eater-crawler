from goto_eat_scrapy.spiders.abstract_liny import AbstractLinySpider

class ShigaSpider(AbstractLinySpider):
    """
    usage:
      $ scrapy crawl shiga -O shiga.csv
    """
    name = 'shiga'
    base_url = 'https://gotoeat-shiga.liny.jp/map/api/data.json'

    x_min = 34.8
    x_max = 35.6
    y_min = 135.7
    y_max = 136.5
    step = 0.015
