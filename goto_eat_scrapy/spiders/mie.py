import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class MieSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl mie -O mie.csv
    """
    name = 'mie'
    allowed_domains = [ 'area34.smp.ne.jp' ]   # 推理の絆...

    limit = 100
    table_id = 26722

    start_urls = [
        f'https://area34.smp.ne.jp/area/table/{table_id}/AikX5e/M?detect=%94%bb%92%e8&_limit_{table_id}={limit}&S=phneq2lbrgkg',
    ]

    # 企業サイトなので(それもどうかと思うが…) 一応気を使う
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 2,    # 詳細ページまで見ないといけないので(4000件前後だから許して…)
    }

    def parse(self, response):
        # 各加盟店情報を抽出
        self.logzero_logger.info(f'💾 url = {response.request.url}')
        for article in response.xpath(f'//table[@id="smp-table-{self.table_id}"]//tr[contains(@class, "smp-row-data")]'):
            url = article.xpath('.//td[contains(@class, "smp-cell-col-3")]/a[@target="_self"]/@href').get()
            yield scrapy.Request(response.urljoin(url), callback=self.detail)

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//table[@class="smp-pager"]//td[@class="smp-page smp-current-page"]/following-sibling::td/a/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        self.logzero_logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

    def detail(self, response):
        item = ShopItem()
        self.logzero_logger.info(f'💾 url(detail) = {response.request.url}')
        item['detail_page'] = response.request.url
        for tr in response.xpath('//table[@class="smp-card-list"]'):
            item['shop_name'] = tr.xpath('.//tr/th[contains(text(), "店舗名")]/following-sibling::td/text()').get().strip()

            place_list = tr.xpath('.//tr/th[contains(text(), "住所情報")]/following-sibling::td/text()').getall()
            item['zip_code'] = place_list[0].strip()
            item['address'] = ''.join(place_list[1:]).strip()

            # MEMO: 「電話番号」だけテーブル構造が壊れてて<tr>タグがないのに注意。ブラウザだと普通にレンダリング表示されるのでハマった…
            item['tel'] = tr.xpath('.//th[contains(text(), "電話番号")]/following-sibling::td/text()').get().strip()

            item['area_name'] = tr.xpath('.//tr/th[contains(text(), "店舗エリア")]/following-sibling::td/text()').get().strip()
            item['genre_name'] = tr.xpath('.//tr/th[contains(text(), "業態")]/following-sibling::td/text()').get().strip()
            item['offical_page'] = tr.xpath('.//tr/th[contains(text(), "WEB URL")]/following-sibling::td/a/@href').get()

        self.logzero_logger.debug(item)
        return item

