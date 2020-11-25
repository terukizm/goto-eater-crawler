goto-eater-scrapy
===

# Usage

## pipenv利用

```
$ git clone ...
$ cd goto-eater-scrapy/

$ ls | grep Pipfile
Pipfile
$ pipenv install
(略)

$ pipenv run scrapy crawl tochigi -O tochigi.csv
(略)
$ cat tochigi.csv | wc -l
3270
```

## Docker利用

```
$ git clone ...
$ cd goto-eater-scrapy/

$ ls | grep Dockerfile
Dockerfile
$ IMAGE_NAME=goto-eater-scrapy:LATEST
$ docker build -t $IMAGE_NAME .
(略)
$ docker images $IMAGE_NAME
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
goto-eater-scrapy   LATEST              1f7795025dc4        21 minutes ago      553MB

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
$ pipenv run python -m goto_eat_scrapy.main
    or
$ docker run -it -v `pwd`:/app/ $IMAGE_NAME python -m goto_eat_scrapy.main
```

