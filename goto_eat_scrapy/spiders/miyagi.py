import demjson
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
    area_list = [
        {
            'url': 'https://gte-miyagi.jp/available_aobaku.php',
            'params': {'searchwords': ' ', 'area': '仙台市青葉区', 'ch': 'all'},
        },
        {
            'url': 'https://gte-miyagi.jp/available_miyaginoku.php',
            'params': {'searchwords': ' ', 'area': '仙台市宮城野区', 'ch': 'all'},
        },
        {
            'url': 'https://gte-miyagi.jp/available_wakabayashiku.php',
            'params': {'searchwords': ' ', 'area': '仙台市若林区', 'ch': 'all'},
        },
        {
            'url': 'https://gte-miyagi.jp/available_taihakuku.php',
            'params': {'searchwords': ' ', 'area': '仙台市太白区', 'ch': 'all'},
        },
        {
            'url': 'https://gte-miyagi.jp/available_izumiku.php',
            'params': {'searchwords': ' ', 'area': '仙台市泉区', 'ch': 'all'},
        },
        {
            # 宮城県北部
            'url': 'https://gte-miyagi.jp/available03.php',
            'params': {'searchwords': ' ', 'area': 'all', 'ch': 'all'},
        },
        {
            # 宮城県南部
            'url': 'https://gte-miyagi.jp/available04.php',
            'params': {'searchwords': ' ', 'area': 'all', 'ch': 'all'},
        }
    ]

    def start_requests(self):
        for row in self.area_list:
            url = row['url']
            params = row['params']
            self.logzero_logger.info(f'💾 params = {params}')
            yield scrapy.FormRequest(url, \
                    callback=self.parse, method='POST', \
                    formdata=params)

    def parse(self, response):
        # エリア名取得
        text = response.xpath('//div[@class="wrap"]/div[@class="cont"]/h2/span/text()').extract_first()
        m = re.search(r'\[\s(?P<area_name>.*)\s\]', text)
        area_name = m.group('area_name')

        # マーカー表示用に使われている<script> タグ中の"const data = [ ... ];" を抽出
        # JSONではないので(javascript Object形式)、demjsonで変換して利用
        text = response.xpath("//script[contains(., 'const data = [')]/text()").extract()[0]
        m = re.search(r'const data = (?P<js_data>\[.*?\]);', text, re.DOTALL)
        js_data_text = m.group('js_data')
        # MEMO: js中のデータと突き合わせたとき、htmlタグの有無で一致しないことがある。
        # jsの中身についてもShopItemを通した形に変換し(このときにHTMLタグがstripされる)、書式を統一
        data_item_list = [ ShopItem(shop_name=row['name'].strip(), address=row['content'].strip(), provided_lat=row['lat'], provided_lng=row['lng']) \
            for row in (demjson.decode(js_data_text) if js_data_text else []) ]

        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//div[@class="SLCont"]//dl[@class="shopList"]'):
            item = ShopItem()
            item['area_name'] = area_name
            item['shop_name'] = article.xpath('.//dt/text()').get().strip()
            item['genre_name'] = article.xpath('.//dd[1]/span[2]/text()').get().strip()

            # MEMO: アパヴィラホテルの住所に<>が含まれており、それをxpathで取得したときにタグ扱いにされてしまって(text()で取れない)
            # <>内が抜け落ちる。ただ、そもそも住所データとして<>が入ってきても、出力時にちゃんと&lt;&gt;に変換して出力すべきなのでは… という気持ちも…
            place = ' '.join(article.xpath('.//dd[2]/span[2]/text()').getall())
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address').strip()
            item['zip_code'] = m.group('zip_code').strip()
            item['tel'] = article.xpath('.//dd[3]/span[2]/text()').get().strip()

            # MEMO: 本来は@hrefで取りたいが、aリンクが貼られてないのもあるため(2020/11/28)
            item['official_page'] = article.xpath('.//dd[4]/span[@class="url"]/text()').get()

            # jsのname要素が完全一致、jsのcontent要素に含まれる住所が部分一致するものを抽出
            match = [jsdata for jsdata in data_item_list \
                if (item['shop_name'] == jsdata['shop_name'] and (item['address'] in jsdata['address'])) ]

            if match:
                item['provided_lat'] = match[0]['provided_lat']
                item['provided_lng'] = match[0]['provided_lng']
            elif 1 < len(match):
                self.logzero_logger.warn(f'🔥 宮城県のlatlng取得において、店名と住所で重複しているものがありました: {match}')
            else:
                self.logzero_logger.warn(f'🔥 宮城県のlatlng取得において、店名と住所が一致しないものがありました: item={item} @「{area_name}」')

            yield item
