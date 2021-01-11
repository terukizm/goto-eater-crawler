goto-eater-crawler
===

各都道府県のGoToEat公式サイトで公開されている、GoToEat食事券の加盟店を取得するクローラーです。
Scrapyをベースにしていますが、北海道と大分県については個別に実装しています。

# Usage

## Scrapyコマンドで実行

ログ出力、成果物出力等はScrapyコマンドに準拠。

### poetry利用

```
$ git clone git@github.com:terukizm/goto-eater-crawler.git
$ cd goto-eater-crawler/

$ ls | grep pyproject.toml
pyproject.toml
$ poetry install
(略)

$ poetry run scrapy crawl tochigi -O tochigi.csv
(略)
$ cat tochigi.csv | wc -l
(略)
```

### docker-compose利用

```
$ git clone git@github.com:terukizm/goto-eater-crawler.git
$ cd goto-eater-crawler/

$ ls | grep docker-compose.yml
docker-compose.yml
$ docker-compose build
(略)

$ docker-compose run crawler scrapy crawl tochigi -O tochigi.csv
(略)
$ cat tochigi.csv | wc -l
(略)
```

## 一括実行

以下を順番にすべて実行します。成果物は`data/`以下に出力されます。

* 全Spiderの並列実行
  * Scrapy以外のクローラー(北海道、大分県)の実行(Not並列)
* クロール結果のCSVをソート(店舗名、住所、(ジャンル))

```
$ poetry run python main.py
    or
$ docker-compose run crawler python main.py
```

`--target` を加えることで任意の都道府県だけ実行できます。,区切りで複数指定も可能。

```
$ poetry run python main.py --target fukuoka

$ docker-compose run crawler python main.py --target tochigi,oita,gunma
```

## キャッシュ

Scrapyのhttpcacheを期限切れなし(`settings.HTTPCACHE_EXPIRATION_SECS = 0`)で有効にしているため、**2回目以降の実行結果は必ず同じものになります。**
キャッシュを効かせたくない場合は設定を変えるか、`.scrapy/`以下を削除してください。
Scrapyを使っていない北海道、大分県も取得したHTMLの内容を`.scrapy/`以下にキャッシュしているので、必要なら同様に削除してください。


# GitHub Actionsによる定期実行について

[goto-eater-data](https://github.com/terukizm/goto-eater-data)において、以下の条件で実行しています。

* 公的に公開・運用されている、公式なGoToEatのサイトからのみ情報を取得
  * UserAgentで`goto-eater-crawler`を指定
* 1秒間に1リクエストを最大値として、シリアルにアクセス
  * 基本的には3秒おきのリクエストとして、深夜時間帯(25:03〜)で実行
    * 4〜5h程度の実行時間
* 成果物は上記リポジトリに保存、別途[goto-eater-csv2geojson]でgeojson形式に変換


# 対応外の都道府県について

徳島県についてはデフォルトでは処理しないようになっています。
これは公式サイトの検索画面に「本サイトのコンテンツの無断転載を禁じます。」という一文があるためです。

## 結果CSVのソート

poetryでcsvkitが入っているので、csvsortコマンドを使うと楽。

```
$ find ./data/csvs -type f -name "*.csv" -print0 | xargs -0 -I {} sh -c 'poetry run csvsort -c 1 -d "," -q \" {} > {}.sorted && mv {}.sorted {}'
```

タスクライナーも設定してあるので、1件くらいなら以下でもOK.

```
$ poetry run task csvsort tokyo.csv > tokyo.csv.sorted
```

