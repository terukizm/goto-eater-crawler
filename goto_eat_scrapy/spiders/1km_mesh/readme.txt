以下のデータセットを利用させていただいています。

都道府県別1kmメッシュ
https://www.geospatial.jp/ckan/dataset/npli-pref-1km

* 千葉県(5292メッシュ)
    * https://www.geospatial.jp/ckan/dataset/ee0203ee-d526-419c-b894-950b03a1ecd0/resource/c087134b-589e-4e9d-be92-a70c205f733b/download/12chiba1km.geojson
* 神奈川県(2583メッシュ)
    * https://www.geospatial.jp/ckan/dataset/ee0203ee-d526-419c-b894-950b03a1ecd0/resource/3a4560bc-a810-4db7-8484-445476f71207/download/14kanagawa1km.geojson
* 滋賀県(4051メッシュ)
    * https://www.geospatial.jp/ckan/dataset/ee0203ee-d526-419c-b894-950b03a1ecd0/resource/45a70a37-7270-4e97-bf81-3963864d9dc6/download/25shiga1km.geojson

```
$ cat 12chiba1km.geojson| grep coordinates | wc -l
    5292
$ cat 14kanagawa1km.geojson | grep coordinates | wc -l
    2583
$ cat 25shiga1km.geojson | grep coordinates | wc -l
    4051
```

(同様に500mメッシュも提供されていますが、縦横が1/2になるとリクエスト回数がx4となり、実行時間も単純に4倍になるので…)
