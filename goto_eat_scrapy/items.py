# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class ShopItem(scrapy.Item):
    # 必須項目
    shop_name = scrapy.Field()      # 店舗名
    address = scrapy.Field()        # 住所(市区町村以下)
    tel = scrapy.Field()            # 電話番号
    # オプション項目
    genre_name = scrapy.Field()     # ジャンル名
    zip_code = scrapy.Field()       # 郵便番号
    offical_page = scrapy.Field()   # 公式ホームページ
