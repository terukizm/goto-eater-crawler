import re
import scrapy
import json
from logzero import logger

from goto_eat_scrapy.items import ShopItem

class YamagataSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl yamagata -O 06_yamagata.csv
    """
    name = 'yamagata'
    allowed_domains = [ 'yamagata-gotoeat.com' ]    # .comとは

    endpoint = 'https://yamagata-gotoeat.com/wp/wp-content/themes/gotoeat/search.php'

    area_list = [
        '山形市',
        '寒河江市',
        '上山市',
        '村山市',
        '天童市',
        '東根市',
        '尾花沢市',
        '山辺町',
        '中山町',
        '河北町',
        '西川町',
        '朝日町',
        '大江町',
        '大石田町',
        '新庄市',
        '金山町',
        '最上町',
        '舟形町',
        '真室川町',
        '大蔵村',
        '鮭川村',
        '戸沢村',
        '米沢市',
        '南陽市',
        '長井市',
        '高畠町',
        '川西町',
        '小国町',
        '白鷹町',
        '飯豊町',
        '酒田市',
        '鶴岡市',
        '三川町',
        '庄内町',
        '遊佐町',
    ]

    genre_list = [
        'ラーメン',
        'うどん・そば',
        'カレー',
        '居酒屋・創作料理',
        '焼鳥・串揚げ',
        'ダイニングバー・バル',
        '和食・寿司・天ぷら',
        '鉄板・ステーキ',
        '洋食',
        'イタリアン',
        'フレンチ',
        '中華料理',
        '焼肉',
        'アジア・エスニック',
        'お好み焼き・もんじゃ',
        'カフェ・スイーツ',
        'ファミリーレストラン',
        'ファーストフード',
        '定食屋',
        'その他',
    ]

    def start_requests(self):
        params = {'text': '', 'page': '1'}
        yield scrapy.FormRequest(self.endpoint, callback=self.parse, method='POST', formdata=params)


    def parse(self, response):
        # レスポンスはjsonなので直接parse
        data = json.loads(response.body)

        # (参考): htmlは以下のDOM構造にしてから、XPathで抽出
        #
        # <article>
        #   <li>
        #     <ul class="search__result__tag">
        #       <li>鶴岡市</li>
        #       <li>和食・寿司・天ぷら</li>
        #     </ul>
        #     <h2>和食藤川</h2>
        #     <div>997-0034 山形県鶴岡市本町2-15-27</div>
        #     <div>TEL : 023-522-8821</div>
        #   </li>
        #   <li>....<li>
        #   <li>....<li>
        # </article>

        html = scrapy.Selector(text=f'<article>{data["html"]}</article>')
        for article in html.xpath('//article/li'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//h2/text() | .//h2/a/text()').get().strip()

            place = article.xpath('.//div[1]/text()').get().strip()
            m = re.match(r'(?P<zip_code>.*?)\s(?P<address>.*)', place)
            item['address'] = m.group('address')
            item['zip_code'] = m.group('zip_code')

            tel = article.xpath('.//div[2]/text()').get()
            item['tel'] = tel.replace('TEL : ', '') if tel else None

            # 「ジャンル名」 (例: "その他")
            for tag in article.xpath('.//ul[@class="search__result__tag"]/li/text()'):
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

        # 最後のページを表示させても「次へ(最後へ)」の出し分けがされてないので、
        # 「activeのページ=次へで表示させるページ」となったときに終了
        pager = scrapy.Selector(text=data["pager"])
        active_page = pager.xpath('//div[@class="search__pager"]/ul/li[@class="search__pager__link active"]/@data-page').get()
        next_page = pager.xpath('//div[@class="search__pager"]/div[contains(text(),"次へ")]/@data-page').get()

        # (参考): pagerは以下のDOM構造
        #
        # <div class="search__pager">
        #   <div class="search__pager__link seach__pager__small" data-page="1">最初へ</div>
        #   <div class="search__pager__link seach__pager__btn" data-page="1">前へ</div>
        #   <ul>
        #     <li>1</li>
        #     <li class="search__pager__link active" data-page="2">2</li>
        #     <li>...</li>
        #   </ul>
        #   <div class="search__pager__link search__pager__btn" data-page="3">次へ</div>
        #   <div class="search__pager__link seach__pager__small" data-page="85">最後へ</div>
        # </div>

        if active_page == next_page:
            logger.info('💻 finished. last page = ' + active_page)
            return

        logger.info(f'next_page = {next_page}')
        params = {'text': '', 'page': next_page}
        yield scrapy.FormRequest(self.endpoint, callback=self.parse, method='POST', formdata=params)
