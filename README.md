goto-eater-crawler
===

# Usage

## poetry利用

```
$ git clone ...
$ cd goto-eater-crawler/

$ ls | grep Pipfile
Pipfile
$ poetry install
(略)

$ poetry run scrapy crawl tochigi -O tochigi.csv
(略)
$ cat tochigi.csv | wc -l
3270
```

## Docker利用

```
$ git clone ...
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

## 一括実行

以下の3点を順番にすべて実行。

* 全Spiderの並列実行
* Scrapy以外のクローラー(北海道、大分県)の並列実行
* クロール結果のCSVをソート(店舗名、住所、(ジャンル))

```
$ poetry run python -m goto_eat_scrapy.main
    or
$ docker run -it -v `pwd`:/app/ $IMAGE_NAME python -m goto_eat_scrapy.main
```

