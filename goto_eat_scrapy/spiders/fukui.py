import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class FukuiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl fukui -O fukui.csv
    """
    name = 'fukui'
    allowed_domains = [ 'gotoeat-fukui.com' ] # .comとは

    def start_requests(self):
        params = {'Keyword': '', 'Action': 'text_search'}
        yield scrapy.FormRequest('https://gotoeat-fukui.com/shop/search.php', \
            callback=self.search, method='POST', \
            formdata=params)

    def search(self, response):
        # 福井県は検索結果のページングなし
        self.logzero_logger.info(f'💾 url(search) = {response.request.url}')
        for article in response.xpath('//div[@class="result"]/ul/li'):
            url = article.xpath('.//a/@href').get().strip()
            yield scrapy.Request(response.urljoin(url), callback=self.detail)

    def detail(self, response):
        self.logzero_logger.info(f'💾 url(detail) = {response.request.url}')
        item = ShopItem()
        item['shop_name'] = response.xpath('//div[@id="contents"]/h3/text()').get().strip()
        item['area_name'] = response.xpath('//div[@id="contents"]/div[@class="icon"]/span[@class="area"]/text()').get().strip()
        item['detail_page'] = response.request.url

        for dl in response.xpath('//div[@id="contents"]/dl'):
            # MEMO: ジャンル指定がされていない(dt[1]が空の)データ、「グルメ民宿 はまもと」があり、その場合following-siblingが変なところ
            # (dd/text()の値が存在する「住所」？)を見に行ってしまうので、暫定的にジャンル部分だけ直指定で実装
            # 参考: https://gotoeat-fukui.com/shop/?id=180097  (にしても画像がうまそうでつらい)

            genre_name = dl.xpath('.//dt[1]/dd/text()').get()
            genre_name = genre_name.strip() if genre_name else ''   # はまもとだけの例外対応
            item['genre_name'] = genre_name.replace('、', '|')  # 複数ジャンル指定あり
            # 元データが修正されれば以下の実装でよい
            # genre_name = dl.xpath('.//dt[contains(text(), "ジャンル")]/following-sibling::dd/text()').get().strip()

            item['tel'] = dl.xpath('.//dt[contains(text(), "電　　話")]/following-sibling::dd/a/text()').get().strip()
            item['address'] = dl.xpath('.//dt[contains(text(), "住　　所")]/following-sibling::dd/text()').get().strip()
            item['opening_hours'] = dl.xpath('.//dt[contains(text(), "営業時間")]/following-sibling::dd/text()').get().strip()
            item['closing_day'] = dl.xpath('.//dt[contains(text(), "定 休 日")]/following-sibling::dd/text()').get().strip()
            item['offical_page'] = dl.xpath('.//dt[contains(text(), "HP・SNS")]/following-sibling::dd/text()').get()

        self.logzero_logger.debug(item)
        return item
