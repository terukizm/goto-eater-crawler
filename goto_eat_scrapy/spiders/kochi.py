
import scrapy
import json
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class KochiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl kochi -O kochi.csv
    """
    name = 'kochi'
    allowed_domains = [ 'gotoeat-kochi.jp' ]

    start_urls = [
        'https://www.gotoeat-kochi.com/js/shop_list.php',   # jsonが帰ってくる
    ]

    def parse(self, response):
        # json形式なので、response.body(bytes)を直接読める
        for row in json.loads(response.body):
            # おそらく
            #   0: area_code,
            #   1: area_name,
            #   2: genre_code,
            #   3: genre_name,
            #   4: ???,
            #   5: shop_name,
            #   6: shop_name_kana,
            #   7: address,
            #   8: tel
            item = ShopItem(
                area_name = row[1],
                genre_name = row[3],
                shop_name = row[5],
                address = row[7],
                tel = row[8],
            )

            # MEMO: 基本的に店舗名中に含まれるHTMLタグは全部取り除く方式にしているが、
            # 高知の"<きてみいや>"さんだけが店名に<>を含むため誤ってstripされてしまう。
            # 公式HPを見ると別に<>が必須というわけではなさそうなので、例外的に対応している…
            # (これに限らず店舗名には、意外と変な名前の店が多いので、ちょっと怖い感じはある…)

            # TODO: クロール結果はjsonかなんかで出す ->  その後でデータクレンジングをかける ->
            # 最後にcsv2geojsonに通す、みたいにすべきかもしれない (それでも例外対応は要るが)
            item['shop_name'] = item['shop_name'].replace('<きてみいや>', '　きてみいや')

            yield item
