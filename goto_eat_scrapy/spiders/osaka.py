import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.exceptions import ScrapingError

class OsakaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl osaka -O output.csv
    """
    name = 'osaka'
    allowed_domains = [ 'goto-eat.weare.osaka-info.jp' ] # weareって要る？

    # https://goto-eat.weare.osaka-info.jp/gotoeat/ から「すべてのエリア」「すべてのジャンル」で検索した結果。つよい(確信)
    start_urls = ['https://goto-eat.weare.osaka-info.jp/gotoeat/?search_element_0_0=2&search_element_0_1=3&search_element_0_2=4&search_element_0_3=5&search_element_0_4=6&search_element_0_5=7&search_element_0_6=8&search_element_0_7=9&search_element_0_8=10&search_element_0_9=11&search_element_0_cnt=10&search_element_1_cnt=17&search_element_2_cnt=1&s_keyword_3=&cf_specify_key_3_0=gotoeat_shop_address01&cf_specify_key_3_1=gotoeat_shop_address02&cf_specify_key_3_2=gotoeat_shop_address03&cf_specify_key_length_3=2&searchbutton=%E5%8A%A0%E7%9B%9F%E5%BA%97%E8%88%97%E3%82%92%E6%A4%9C%E7%B4%A2%E3%81%99%E3%82%8B&csp=search_add&feadvns_max_line_0=4&fe_form_no=0']

    # ジャンルはタグで管理されてるが、地域名(泉州とか)も一緒にタグ管理されてて区別できないので…
    genre_list = ['居酒屋', '和食', '寿司・魚料理', 'うどん・そば', '鍋', 'お好み焼き・たこ焼き', 'ラーメン・つけ麺',
        '郷土料理', '洋食・西洋料理', 'カレー', '焼肉・ホルモン', 'イタリアン・フレンチ', '中華料理', 'アジア・エスニック料理',
        'カフェ・スイーツ', 'ホテルレストラン', 'その他']
    area_list = ['キタ', 'ミナミ', '大阪城', 'あべの・天王寺', 'ベイエリア', '北摂', '北河内', '中河内','南河内', '泉州']

    def parse(self, response):
        # 各加盟店情報を抽出
        base = '//div[@class="search_result_box"]/ul'
        for i, _ in enumerate(response.xpath(f'{base}/li'), 1):
            item = ShopItem()
            # 「店舗名」 (例: "なか卯　ハイパーアロー松ヶ丘店")
            # MEMO: 珉珉上新庄駅前店だけ店名入ってないんすけど…
            item['shop_name'] = response.xpath(f'{base}/li[{i}]/p[@class="name"]/text()').extract_first()
            # 「ジャンル名」 (例: "その他")
            for tag in response.xpath(f'{base}/li[{i}]/ul[@class="tag_list"]/li/text()').extract():
                # 完全一致するタグがあればそれを設定(それ以外のタグについては地域名としてskip)
                # MEMO: 一つの店に複数のジャンルタグが設定されている場合は想定していない(大阪の場合はない…はず…？)
                # 他の自治体では見かけたような気がするので、そんときはどうするかな… (CSVのカラム内で拡張かな…)
                if tag in self.genre_list:
                    item['genre_name'] = tag
                    break
                if tag not in self.area_list:
                    raise ScrapingError(f'想定していない、不明なタグ 「{tag}」')
            # tableタグ部分の抽出
            item = self.__parse_table(f'{base}/li[{i}]', response, item)
            # MEMO: 詳細ページまで回せば公式ページのURLが取れるが、それだけのためにやるか…？って気がしてきたのでしない
            # 2020/11/11現在で819ページもあるし…
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//div[@role="navigation"]//a[@rel="next"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

    def __parse_table(self, base: str, response, item: ShopItem):
        """
        tableタグ部分の項目。テーブル中の項目が個別に色々あるので適当に処理
        """
        # 可変レイアウトにはなってない(と思う)ので多分4行超えることはない(はず)
        for i in range(1, 4):
            try:
                # th部分をkey名として処理(生htmlにtbodyがないので注意)
                key = response.xpath(f'{base}/table/tr[{i}]/th/text()').extract_first()
                if key is None:
                    break
                key = key.strip()
                if key == '住所':
                    text = response.xpath(f'{base}/table/tr[{i}]/td/text()').extract()
                    item['zip_code'] = text[0].strip()
                    item['address'] = re.sub(r'\s', '', text[1])
                elif key == 'TEL':
                    item['tel'] = response.xpath(f'{base}/table/tr[{i}]/td/text()').extract_first()
                elif key == '営業時間':
                    item['opening_hours'] = response.xpath(f'{base}/table/tr[{i}]/td/text()').extract_first()
                elif key == '定休日':
                    item['closing_day'] = response.xpath(f'{base}/table/tr[{i}]/td/text()').extract_first()
                else:
                    # テーブル中に上記以外の項目名が出たら
                    text = response.xpath(f'{base}/table/tr[{i}]/td/text()').extract_first().strip()
                    raise ScrapingError(f'不明なテーブル項目: {key} : {text}')
            except Exception as e:
                logger.error("💀💀💀 [ERR!!] parse Error: " + key)
                raise e

        return item
