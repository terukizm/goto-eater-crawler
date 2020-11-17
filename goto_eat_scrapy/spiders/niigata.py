import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class NiigataSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl niigata -O 15_niigata.csv
    """
    name = 'niigata'
    allowed_domains = [ 'niigata-gte.com' ]     # .comとは

    start_urls = ['https://niigata-gte.com/shop/']

    # ジャンルはタグで管理されてるが、地域名(泉州とか)も一緒にタグ管理されてて区別できないので…
    genre_list = [
        '和食',
        '寿司',
        '割烹',
        '洋食',
        'イタリアン',
        'フレンチ',
        '中華',
        'ラーメン',
        'ファストフード',
        '軽食',
        '喫茶',
        '居酒屋',
        'その他',
    ]
    area_list = [
        '新潟市北区',
        '新潟市東区',
        '新潟市中央区',
        '新潟市江南区',
        '新潟市秋葉区',
        '新潟市南区',
        '新潟市西区',
        '新潟市西蒲区',
        '長岡市',
        '三条市',
        '柏崎市',
        '新発田市',
        '小千谷市',
        '加茂市',
        '十日町市',
        '見附市',
        '村上市',
        '燕市',
        '糸魚川市',
        '妙高市',
        '五泉市',
        '上越市',
        '阿賀野市',
        '佐渡市',
        '魚沼市',
        '南魚沼市',
        '胎内市',
        '聖籠町',
        '弥彦村',
        '田上町',
        '阿賀町',
        '出雲崎町',
        '湯沢町',
        '津南町',
        '刈羽村',
        '関川村',
        '粟島浦村',
    ]

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//div[@id="result"]/div[@class="cont"]'):
            item = ShopItem()
            item['shop_name'] = ''.join(article.xpath('.//h4/text() | .//h4/a/text()').getall()).strip()
            item['offical_page'] = article.xpath('.//h4/a/@href').get()

            place = ''.join(article.xpath('.//p[@class="add"]/text()').getall()).strip()
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')
            item['tel'] = article.xpath('.//p[@class="tel"]/text()').get()

            # 「ジャンル名」 (例: "その他")
            for tag in article.xpath('.//div[@class="tag"]/span/text()'):
                # 完全一致するタグがあれば設定(それ以外のタグは地域名としてskip)
                tagtext = tag.get()
                if not tagtext:
                    continue
                if tagtext in self.genre_list:
                    item['genre_name'] = tagtext
                    break
                if tagtext not in self.area_list:
                    raise ScrapingError(f'想定していない、不明なタグ 「{tagtext}」')

            yield item

        # 「NEXT」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@id="pagination"]/ul/li[@class="next"]/a/@onclick').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        m = re.match(r"^mySubmit\('(?P<page>.*)'\);$", next_page)
        next_page = m.group('page')
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
