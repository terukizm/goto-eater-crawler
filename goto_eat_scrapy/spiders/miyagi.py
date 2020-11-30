import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class MiyagiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl miyagi -O miyagi.csv
    """
    name = 'miyagi'
    allowed_domains = [ 'gte-miyagi.jp' ]

    # @see https://gte-miyagi.jp/available.html
    # 宮城県はページングなし
    start_urls = [
        'https://gte-miyagi.jp/available_aobaku.php',
        'https://gte-miyagi.jp/available_miyaginoku.php',
        'https://gte-miyagi.jp/available_wakabayashiku.php',
        'https://gte-miyagi.jp/available_taihakuku.php',
        'https://gte-miyagi.jp/available_izumiku.php',
        'https://gte-miyagi.jp/available03.php',
        'https://gte-miyagi.jp/available04.php',
    ]

    def parse(self, response):
        # エリア名取得
        text = response.xpath('//div[@class="wrap"]/div[@class="cont"]/h2/span/text()').extract_first()
        m = re.search(r'\[\s(?P<area_name>.*)\s\]', text)
        area_name = m.group('area_name')

        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@class="SLCont"]//dl[@class="shopList"]'):
            item = ShopItem()
            item['area_name'] = area_name
            item['shop_name'] = article.xpath('.//dt/text()').get().strip()
            item['genre_name'] = article.xpath('.//dd[1]/span[2]/text()').get().strip()

            place = ' '.join(article.xpath('.//dd[2]/span[2]/text()').getall())
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address').strip()
            item['zip_code'] = m.group('zip_code').strip()
            item['tel'] = article.xpath('.//dd[3]/span[2]/text()').get().strip()

            # MEMO: 本来は@hrefで取りたいが、aリンクが貼られてないのもあるため(2020/11/28)
            item['offical_page'] = article.xpath('.//dd[4]/span[@class="url"]/text()').get()

            self.logzero_logger.debug(item)
            yield item
