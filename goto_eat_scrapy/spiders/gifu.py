import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class GifuSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl gifu -O 21_gifu.csv
    """
    name = 'gifu'
    allowed_domains = [ 'area34.smp.ne.jp' ]   # 推理の絆...

    # 企業サイトなので(それもどうかと思うが…) 一応気を使う
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 3,
        # 'LOG_LEVEL': 'INFO',
    }

    start_urls = [
        'https://area34.smp.ne.jp/area/table/26960/ADtah6/M?detect=%2594%25bb%2592%25e8&S=phsio2lbsjob&_limit_26960=100',
    ]

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//table[@id="smp-table-26722"]//tr[contains(@class, "smp-row-data")]'):
            url = article.xpath('.//td[contains(@class, "smp-cell-col-3")]/a[@target="_self"]/@href').get()
            yield scrapy.Request(response.urljoin(url), callback=self.detail)

        # リンクボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//table[@class="smp-pager"]//td[@class="smp-page smp-current-page"]/following-sibling::td/a/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        next_page = response.urljoin(next_page)
        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)

    def detail(self, response):
        item = ShopItem()
        logger.debug(response.url) # TODO: 岐阜に限らず、csvにdetailのurl、入れてやるほうがいいかもしれない
        for tr in response.xpath('//table[@class="smp-card-list"]'):
            item['shop_name'] = tr.xpath('.//tr/th[contains(text(), "店舗名")]/following-sibling::td/text()').get().strip()
            item['genre_name'] = tr.xpath('.//tr/th[contains(text(), "業態")]/following-sibling::td/text()').get().strip()
            item['offical_page'] = tr.xpath('.//tr/th[contains(text(), "WEB URL")]/following-sibling::td/a/@href').get()

            place_list = tr.xpath('.//tr/th[contains(text(), "住所情報")]/following-sibling::td/text()').getall()
            item['zip_code'] = place_list[0].strip()
            item['address'] = ''.join(place_list[1:]).strip()

            # 岐阜はテーブル構造が壊れてない
            item['tel'] = tr.xpath('.//tr/th[contains(text(), "電話番号")]/following-sibling::td/text()').get().strip()

        return item

