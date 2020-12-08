goto-eater-crawler
===

# Usage

## poetry利用

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
3270
```
## Docker利用

```
$ git clone git@github.com:terukizm/goto-eater-crawler.git
$ cd goto-eater-crawler/

$ ls | grep Dockerfile
Dockerfile
$ IMAGE_NAME=goto-eater-crawler:LATEST
$ docker build -t $IMAGE_NAME .
(略)
$ docker images $IMAGE_NAME
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
goto-eater-crawler   LATEST              4523bbf6c7a7        17 seconds ago      1.16GB

$ docker run -it -v `pwd`:/app/ $IMAGE_NAME scrapy crawl tochigi -O tochigi.csv
(略)

$ cat tochigi.csv | wc -l
3270
```

## docker-compose利用

```
$ git clone git@github.com:terukizm/goto-eater-crawler.git
$ cd goto-eater-crawler/
$ docker-compose build
$ docker-compose run crawler scrapy crawl tochigi -O tochigi.csv
$ cat tochigi.csv | wc -l
3270
```

## 一括実行

以下の3点を順番にすべて実行。

* 全Spiderの並列実行
* Scrapy以外のクローラー(北海道、大分県)の並列実行
* クロール結果のCSVをソート(店舗名、住所、(ジャンル))

```
$ poetry run python -m goto_eat_scrapy.main
    or
$ docker run -it -v `pwd`:/app/ $IMAGE_NAME python -m goto_eat_scrapy.main
    or
$ docker-compose run crawler python -m goto_eat_scrapy.main
```


# GitHub Actionsによる定期実行について

以下の条件で実行しています。

* 公的に公開・運用されている、公式なGoToEatのサイトからのみ情報を取得
* 1秒間に1リクエストを最大値として、シリアルにアクセス
  * 基本的には3秒おきのリクエストとして、深夜時間帯(23:00〜)で実行
* UserAgentで`xxx`を指定
