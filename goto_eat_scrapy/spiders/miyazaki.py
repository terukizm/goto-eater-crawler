import re
import scrapy
from goto_eat_scrapy.items import ShopItem
from goto_eat_scrapy.spiders.abstract import AbstractSpider


class MiyazakiSpider(AbstractSpider):
    """
    usage:
      $ scrapy crawl miyazaki -O miyazaki.csv
    """

    name = "miyazaki"
    allowed_domains = ["premium-gift.jp"]
    start_urls = ["https://premium-gift.jp/gotoeatmiyazaki/use_store"]

    def parse(self, response):
        self.logzero_logger.info(f"💾 url = {response.request.url}")
        for article in response.xpath('//section[@class="l-store-section"]//div[@class="store-card__item"]'):
            item = ShopItem()

            # 宮崎は"/"もしくは"／"区切りで「店舗名部分に」ジャンル情報を無理やり入れているため、その書式になっていればジャンル名として利用する
            text = " ".join(article.xpath('.//h3[@class="store-card__title"]/text()').getall()).strip()
            m = re.match(r"(?P<shop_name>.*)(\/|／)+(?P<genre_name>.*)", text)
            item["shop_name"] = m.group("shop_name") if m else text
            item["genre_name"] = m.group("genre_name") if m else None

            place = (
                article.xpath('.//table/tbody/tr/th[contains(text(), "住所：")]/following-sibling::td/text()')
                .get()
                .strip()
            )
            m = re.match(r"〒(?P<zip_code>.*?)\s(?P<address>.*)", place)
            item["address"] = m.group("address")
            item["zip_code"] = m.group("zip_code")

            tel = (
                article.xpath('.//table/tbody/tr/th[contains(text(), "電話番号：")]/following-sibling::td/text()')
                .get()
                .strip()
            )
            item["tel"] = "" if tel == "-" else tel

            item["official_page"] = article.xpath(
                './/table/tbody/tr/th[contains(text(), "URL：")]/following-sibling::td/a/@href'
            ).get()
            item["detail_page"] = article.xpath('.//a[@class="store-card__button"]/@href').get().strip()

            # MEMO: 詳細ページの「店舗からのお知らせ」欄に営業時間、定休日が自由書式で記入されているが、とりあえず見送り

            yield item

        # 「次へ」がなければ(最終ページなので)終了
        next_page = response.xpath('//nav[@class="pagenation"]/a[contains(text(),"次へ")]/@href').extract_first()
        if next_page is None:
            self.logzero_logger.info("💻 finished. last page = " + response.request.url)
            return

        m = re.match(r"^javascript:on_events\('page',(?P<page>\d+)\);$", next_page)
        next_page = "https://premium-gift.jp/gotoeatmiyazaki/use_store?events=page&id={}&store=&addr=&industry=".format(
            m.group("page")
        )
        self.logzero_logger.info(f"🛫 next url = {next_page}")

        yield scrapy.Request(next_page, callback=self.parse)
