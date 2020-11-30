import re
import scrapy
import pathlib
import pandas as pd
from goto_eat_scrapy import settings
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider

class naraSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl nara -O nara.csv
    """
    name = 'nara'
    allowed_domains = [ 'premium-gift.jp' ]
    start_urls = ['https://premium-gift.jp/nara-eat']

    def parse(self, response):
        # Topページからリンクを取る(多分最新版が最初に来るだろうという決め打ち)
        xlsx_url = response.xpath('//section[@class="news-list"]//a[contains(text(), "Excel形式")]/@href').extract_first()
        yield scrapy.Request(xlsx_url, callback=self.parse_from_xlsx)

    def parse_from_xlsx(self, response):
        cache_dir = pathlib.Path(__file__).parent.parent.parent / '.scrapy' / settings.HTTPCACHE_DIR / self.name
        tmp_xlsx = str(cache_dir / '利用店舗一覧.xlsx')

        with open(tmp_xlsx, 'wb') as f:
            f.write(response.body)
        self.logzero_logger.info(f'💾 saved pdf: {response.request.url} > {tmp_xlsx}')

        df = pd.read_excel(tmp_xlsx, sheet_name='リスト').fillna({'電話番号': '', 'URL': ''})
        for _, row in df.iterrows():
            item = ShopItem()
            item['area_name'] = row['エリア'].strip()
            item['shop_name'] = ' '.join(row['店舗名称'].splitlines()) # 店舗名に改行が入ってるものがあるので半角スペースに置換
            item['genre_name'] = row['カテゴリー'].strip()
            item['address'] = row['住所'].strip()
            item['tel'] = row['電話番号']
            item['official_page'] = row['URL']

            self.logzero_logger.debug(item)
            yield item
