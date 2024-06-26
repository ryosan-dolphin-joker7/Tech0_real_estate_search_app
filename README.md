# Tech0_real_estate_search_app

不動産の賃貸情報検索アプリのサンプルコードです。<br>
※これはあくまで「個人学習」の記録としており、商用利用ではありません。<br>
※参考にする場合は、各種サイトなどの利用規約をよく読み、個人の判断で参考にしてください。<br>

<br>

```
Tech0_real_estate_search_app/
│
├── .env               # 環境変数のダミーデータ
├── .gitignore         # git-hubプッシュ時のファイル対象除外設定
├── README.md
├── main.py            # メインのpythonファイル　これをStreamlit sharingでデプロイします
│
├── function/
│   ├── db_search_function.py   # フロントエンドに不要な処理を関数でまとめています
│   ├── googlemap_api.py        # Google map API を使って緯度と経度情報を取得します
│   └── create_df.py            # 物件のデータベースのサンプルデータです
│
└── scraping/
    ├── scraping_real_estate.ipynb     # ホームズのwebサイトをスクレイピングするファイル
    ├── estate_list2.db                # スクレイピングした物件データのデータベース
    ├── scraping_starbucks2.ipynb      # スターバックスをスクレイピングするファイル
    ├── starbucks_list2.db             # スターバックスのデータベース
    ├── Step3_Scraping_sample01.py
    └── Step3_Scraping.ipynb
```

<br>
    
## 🔳 データ収集・加工・保存コード scraping
```
Step3_Scraping.ipynb       # 不動産データのスクレイピング・データ加工等の各コード機能確認用  
Step3_Scraping_sample01.py # 上記の機能の関数化・統合化                     
```

参考) https://www.youtube.com/watch?v=uBy7F4Wd9cE&t=948s

## 補足.

gitignore を行う際には、git のキャッシュが残っている場合には反映されない場合があるので注意  
キャッシュを削除するコマンドが必要  
参考) https://qiita.com/yutosa3/items/25ab031c8061e8c9a4c4

gitignore 内に/grspread_key.json とあるが基本別のフォルダに保存、環境変数のパス指定から読み込みを行うため本来はコードと同じディレクトリにも置かない。

<br>
<br>

## 🔳 物件検索・表示アプリコード app

```
Step3_Streamlit.py                # 物件検索・表示アプリ
```

![Image 2](https://imgur.com/Bdxw09e.jpg)

![Image 1](https://imgur.com/8MaMreT.jpg)
