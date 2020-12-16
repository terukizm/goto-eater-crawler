# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
import re
import w3lib

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem as DropItemException
from goto_eat_scrapy.items import ShopItem

def normalize_text(text):
    if not text:
        return text

    text = w3lib.html.remove_tags(text)
    text = ''.join(text.splitlines())

    return text.strip()


class GotoEatScrapyPipeline:
    def process_item(self, item, spider):
        # バリデーションと正規化(改行コード削除、HTMLタグ削除、strip()等)
        self._validate(item)
        item = self._normalize(item)

        # ログ出力
        spider.logzero_logger.debug(item)
        return item

    def _normalize(self, item):
        # 改行コード削除とHTMLタグの削除を行う項目
        for attr in ['shop_name', 'address', 'opening_hours', 'closing_day']:
            if (text:= item.get(attr)):
                item[attr] = normalize_text(text)

        # strip()のみの項目
        for attr in ['genre_name', 'area_name']:
            if (text:= item.get(attr)):
                item[attr] = text.strip()

        return item

    def _validate(self, item):
        # 必須チェック
        for attr in ['shop_name', 'address']:
            if not item.get(attr):
                raise DropItemException(f'{attr}は必須です。')
        # 書式エラー(未入力を許可)
        # (MEMO: DropItemExceptionが発生した場合、クローリング処理自体は止まらず該当データだけが落ちる)
        if (tel := item.get('tel')) and not re.match(r'^0\d{9,10}$', str(tel).replace('-', '')):
            # MEMO: 最初は phonenumbers.is_valid_number() で実装したが、入力データのいい加減さから見て
            # 整合性チェックとして厳しすぎて落ちてしまう可能性があるので、あえて雑なやり方(10桁 or 11桁)にしている
            raise DropItemException(f'電話番号の書式が正しくありません。tel={tel}')
        if (zip_code := item.get('zip_code')) and not re.match(r'^\d{7}$', str(zip_code).replace('-', '')):
            # MEMO: 郵便番号も明らかに間違ったデータが入ってたらコケる程度にしておく
            raise DropItemException(f'郵便番号の書式が正しくありません。zip_code={zip_code}')


if __name__ == "__main__":
    # usage:
    # $ python -m goto_eat_scrapy.pipelines

    # TODO: ちゃんとテストを書くべき

    ## invalid
    # pipeline = GotoEatScrapyPipeline()
    # item = ShopItem()
    # item = ShopItem(shop_name='')
    # item = ShopItem(shop_name='a', address='')
    # item = ShopItem(shop_name='a', address='b', tel='invalid')
    # item = ShopItem(shop_name='a', address='b', tel='012-345-678')
    # item = ShopItem(shop_name='a', address='b', tel='1200-345-678')
    # item = ShopItem(shop_name='a', address='b', zip_code='invalid')
    # item = ShopItem(shop_name='a', address='b', zip_code='222-123')
    # pipeline._validate(item)

    ## valid
    # item = ShopItem(shop_name='a', address='b', tel='090-1234-5678')
    # item = ShopItem(shop_name='a', address='b', tel='09012345678')
    # item = ShopItem(shop_name='a', address='b', zip_code='012-3456')
    # item = ShopItem(shop_name='a', address='b', zip_code='0123456')
    # pipeline._validate(item)

    res = normalize_text('山下町12-12\r\n  一二三ビル1F')
    assert '山下町12-12  一二三ビル1F' == res, res

    print('success!!')
