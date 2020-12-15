
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class KagoshimaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl kagoshima -O kagoshima.csv
    """
    name = 'kagoshima'
    allowed_domains = [ 'kagoshima-cci.or.jp' ]
    start_urls = ['http://www.kagoshima-cci.or.jp/?p=20375']

    # FIXME: 鹿児島は2020/12/04？にpdfをやめてhtmlにしてくれたが、おそらく元のExcelから行を非表示にしたものを
    # ExcelのWebページ発行ウィザードとやらで出力しているだけなので、HTMLソースを見ると重複した内容が含まれている。
    # 件数から見ておそらく「鹿児島市全域」と「それ以外」で２つのファイルがあり、それを出し分けしてると思うので、
    # そんな感じでやっていってる(kcciさんの苦労が偲ばれる…)
    area_list = [
        '鹿児島市全域',
        # '〇薩摩川内市',
        # '〇鹿屋市',
        # '〇枕崎市',
        # '〇阿久根市',
        # '〇奄美市',
        # '〇南さつま市',
        # '〇出水市',
        # '〇指宿市',
        # '〇いちき串木野市',
        # '〇霧島市',
        # '〇姶良市',
        '〇その他地域',
    ]
    not_target_area_list = [
        '天文館地区',
        '鹿児島中央駅地区',
        '中央地区',
        '上町地区',
        '鴨池地区',
        '城西地区',
        '武・田上地区',
        '谷山北部地区',
        '谷山地区',
        '伊敷・吉野地区',
        '桜島・吉田・喜入・松元・郡山地区',
        '◇食事券購入情報はこちら',
    ]

    def parse(self, response):
        for p in response.xpath('//div[@id="contents_layer"]/span/p'):
            area_name = p.xpath('.//a/text()').get()
            if not area_name:
                continue
            if area_name in self.not_target_area_list:
                continue
            if area_name in self.area_list:
                url = p.xpath('.//a/@href').get().strip()
                yield scrapy.Request(url, callback=self.parse_from_area_html, meta={'area_name': area_name})
            else:
                # MEMO: 暫定的にExcelのWebページ発行ウィザードの仕様に合わせてコメントアウト、最後まで本気でこれで行きそうな感じなら実装を直すが、
                # 鹿児島はもう3回くらい出力形式が変わっているので、もう諦めてやっつけ仕事でいく...
                # self.logzero_logger.warning(f'鹿児島商工会議所エラー: 「{area_name}」 is not found.')
                pass

    def parse_from_area_html(self, response):
        area_name = response.meta['area_name']
        for article in response.xpath('//table/tr'):
            if article.xpath('.//td[2]/a[contains(text(), "検索")]').get():
                item = ShopItem()
                # MEMO: 店舗名、住所に改行が入ってるものがある(item pipelineで対応)
                item['shop_name'] = article.xpath('.//td[3]/text()').get().strip()
                item['address'] = article.xpath('./td[4]/text()').get().strip()

                # MEMO: エリア名はhtmlから取れなくもないが、Excelベースの表構造なのでしんどい
                # area_list経由で取るのも、実質2データしかなく、それらをdisplay:noneで出し分けしている
                # (おそらく一つのExcelシートを非表示にしたりして出してる)ので大変めんどい
                # 最後まで本気でこのWebページ形式で行く感じだったら、諦めた対応するかも

                # item['genre_name'] = None   # 鹿児島はジャンル情報なし

                self.logzero_logger.debug(item)
                yield item
