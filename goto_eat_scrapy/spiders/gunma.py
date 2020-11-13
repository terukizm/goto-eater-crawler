import re
import scrapy
from logzero import logger
from goto_eat_scrapy.items import ShopItem

class GunmaSpider(scrapy.Spider):
    """
    usage:
      $ scrapy crawl gunma -O output.csv
    """
    name = 'gunma'
    allowed_domains = [ 'gunma-gotoeat-campaign.com' ]

    # HP上は入力制限で同時に3つまでしかジャンル指定ができないようになっている。お作法に従うなら同様に制限させた上で
    # クローリングさせればよいのだが、内部実装的にそれでシステム負荷が減るわけでもなさそうなので、行儀が悪いが
    # クエリいじってジャンル指定なしで検索している。
    # (あと合計件数が合わないのでおそらくカテゴリなしになってるレコードが1件ある。ちょっと気になるのでそれの確認も兼ねて。)
    start_urls = ['https://gunma-gotoeat-campaign.com/shop/?s=&post_type=shop']

    def parse(self, response):
        # 各加盟店情報を抽出
        for article in response.xpath('//section[@id="result"]/article'):
            item = ShopItem()
            item['genre_name'] = article.xpath('.//div[2]/span[@class="shopcat"]/text()').get() # 「舟木亭館林店」だけジャンルがない
            item['shop_name'] = article.xpath('.//div[2]/h3/text()').get().strip()
            item['zip_code'] =  article.xpath('.//div[2]/p[@class="shopadr"]/span/text()').get()[1:]
            item['address'] =  article.xpath('.//div[2]/p[@class="shopadr"]/text()').get().strip()

            # オプション項目
            tel = article.xpath('.//div[2]/p[@class="shoptel"]/text()').get()
            item['tel'] = tel.replace('TEL.', '') if tel else None
            item['offical_page'] = article.xpath('.//div[2]/div[@class="shopinfo"]/a[2]/@href').get()

            yield item

        # 「>」ボタンがなければ(最終ページなので)終了
        next_page = response.xpath('//*[@id="search_page_outer"]//a[@class="next page-numbers"]/@href').extract_first()
        if next_page is None:
            logger.info('💻 finished. last page = ' + response.request.url)
            return

        logger.info(f'🛫 next url = {next_page}')

        yield scrapy.Request(next_page, callback=self.parse)
