import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class GotoeatTochigiSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl tochigi -O output.csv
    """
    name = 'tochigi'
    allowed_domains = [ 'gotoeat-tochigi.jp' ]

    start_urls = ['https://www.gotoeat-tochigi.jp/merchant/index.php?page=1']

    def parse(self, response):
        # 各加盟店情報を抽出
        base = '//*[@id="contents"]/ul[@class="serch_result"]'  # "serch" is not my TYPO...
        for i, _ in enumerate(response.xpath(f'{base}/li'), 1):
            item = ShopItem()
            # 「店舗名」 (例: "幸楽苑　足利店")
            item['shop_name'] = response.xpath(f'{base}/li[{i}]/p[@class="name"]/text()').extract_first().strip()
            # 「ジャンル名」 (例: "ラーメン・餃子")
            item['genre_name'] = response.xpath(f'{base}/li[{i}]/p[@class="name"]/span/text()').extract_first().strip()
            # 「所在地」から「郵便番号」「住所」を取得
            #   (例: "〒326-0335 栃木県 足利市 上渋垂町字伊勢宮364-1") => "326-0335", "足利市 上渋垂町字伊勢宮364-1"
            place = response.xpath(f'{base}/li[{i}]/div[@class="add"]/p[1]/text()').extract_first().strip()
            logger.debug(f'  place={place}')
            # たまに入力ブレがあるので、正規表現とかで適当に処理
            #   (例: スペースなし "〒328-0054 栃木県栃木市平井町659-7")
            #   (例: 都道府県名なし "〒320-0026 宇都宮市 馬場通り1-1-1　シティータワー宇都宮1F")
            #   (例: 郵便番号のハイフンなし "〒3270821 栃木県 佐野市 高萩町1216-2")
            m = re.match(r'〒(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')
            # 「電話番号」 (例: "0284-70-5620"・無入力の場合あり)
            item['tel'] = response.xpath(f'{base}/li[{i}]/div[@class="add"]/p[2]/a/text()').extract_first()
            # 「公式ホームページ」 (例: "https://www.kourakuen.co.jp/"・無入力の場合あり)
            item['offical_page'] = response.xpath(f'{base}/li[{i}]/ul[@class="hp"]//a[contains(text(),"ホームページ")]/@href').extract_first()
            yield item

        # 「次の一覧」がなければ終了
        next_page = response.xpath('//*[@id="contents"]//li[@class="next"]/a/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
