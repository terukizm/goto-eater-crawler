# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import re

import scrapy
import w3lib
from itemadapter import ItemAdapter

from goto_eat_scrapy.items import ShopItem


def normalize_text(text):
    if not text:
        return text

    text = w3lib.html.remove_tags(text)
    text = "".join(text.splitlines())

    return text.strip()


class GotoEatScrapyPipeline:
    def process_item(self, item, spider):
        # 正規化(改行コード削除、HTMLタグ削除、strip()等)
        item = self._normalize(item, spider)
        # ログ出力
        spider.logzero_logger.debug(item)
        return item

    def _normalize(self, item, spider):
        # 改行コード削除とHTMLタグの削除を行う項目
        # MEMO: 岐阜、茨城、三重で使われているシステムでは、official_page(URL)中にHTMLタグが含まれるのがいくつかある
        for attr in ["shop_name", "address", "opening_hours", "closing_day"]:
            if (text := item.get(attr)) :
                item[attr] = normalize_text(text)

        # strip()するだけの項目
        for attr in ["genre_name", "area_name", "tel", "zip_code"]:
            if (text := item.get(attr)) :
                item[attr] = text.strip()

        return item

    def open_spider(self, spider):
        spider.logzero_logger.info(f"🚀 [{spider.name}] start")

    def close_spider(self, spider):
        spider.logzero_logger.info(f"🪂 [{spider.name}]  end ")


if __name__ == "__main__":
    # usage:
    # $ python -m goto_eat_scrapy.pipelines

    res = normalize_text("山下<br>町12-12\r\n  一二三ビル1F")
    assert "山下町12-12  一二三ビル1F" == res, res

    print("success!!")
