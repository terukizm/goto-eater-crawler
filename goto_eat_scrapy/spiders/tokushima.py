import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class TokushimaSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl tokushima -O tokushima.csv
    """
    name = 'tokushima'
    allowed_domains = [ 'gotoeat.tokushima.jp' ]
    start_urls = ['https://gotoeat.tokushima.jp/?s=']

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath('//main[@id="main"]//article'):
            item = ShopItem()
            item['shop_name'] = article.xpath('.//header/h2/text()').get().strip()

            # 「ジャンル」
            # ","区切りで複数指定してるものがあるので、"|" 区切りに変換
            text = ''.join(article.xpath('.//header/text()').getall())
            genre = text.strip().replace('ジャンル：', '')
            item['genre_name'] = '|'.join([s.strip() for s in genre.split(',')])

            # MEMO: 2020/11/18時点の暫定実装、下記データの問題がなければ following-sibling でよい
            # 本来「所在地なし」はありえないが、"富田街ダイニング坊乃"を出力したときだけ、DOM構造が崩れる
            # 例: <dd徳島市富田町2-19</dd>
            # 内部ではHTMLタグ入りのデータを永続化してて、そのデータがおかしいとか…？
            # (コメント機能でチクッたらcomment=5とかだったので、既に何件かレポート行ってる気がする)
            item['address'] = article.xpath('.//div[@class="entry-content"]/dl/dd[1]/text()').get().strip()
            item['closing_day'] = article.xpath('.//div[@class="entry-content"]/dl/dd[2]/text()').get()
            item['opening_hours'] = article.xpath('.//div[@class="entry-content"]/dl/dd[3]/text()').get()
            item['tel'] = article.xpath('.//div[@class="entry-content"]/dl/dd[4]/text()').get()

            # MEMO: detailのURLが取れるが、なんとなく一般公開用ではなさそうなので見なかったことにしておく…
            # たのむぞ運営管理会社の人… (自社のHPから食事券のリンクを貼ったり、見えるところにプライバシーポリシーを張ってるくらいだからいいのか？)
            #item['detail_page'] = article.xpath('.//a[@rel="bookmark"]/@href').get().strip()

            # MEMO: 地域名については結果に表示されないので検索条件から抜いてくるしかない、どうしても必要なら
            # start_urlsを以下のように分けてitem['area_name']に突っ込む
            # start_urls = [ f'https://gotoeat.tokushima.jp/?category_name={url}' for url in ['県東部', '県西部', '県南部'] ]
            # (なお地域名、ジャンル名は複数指定するとちゃんと検索できない (2020/11/30))

            self.logzero_logger.debug(item)
            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@role="navigation"]/div[@class="nav-links"]/a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
