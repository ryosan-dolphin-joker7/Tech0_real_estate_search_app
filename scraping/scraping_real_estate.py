import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime
import numpy as np
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# スクレイピング対象のURLリスト
url_list = [
    'https://suumo.jp/jj/chintai/ichiran/FR301FC005/?fw2=&mt=9999999&cn=9999999&ta=13&et=9999999&sc=13104&shkr1=03&ar=030&bs=040&ct=9999999&shkr3=03&shkr2=03&srch_navi=1&mb=0&shkr4=03&cb=0.0',
    'https://suumo.jp/jj/chintai/ichiran/FR301FC005/?fw2=&mt=9999999&cn=9999999&ta=13&et=9999999&sc=13103&shkr1=03&ar=030&bs=040&ct=9999999&shkr3=03&shkr2=03&srch_navi=1&mb=0&shkr4=03&cb=0.0',
    'https://suumo.jp/jj/chintai/ichiran/FR301FC005/?fw2=&mt=9999999&cn=9999999&ta=13&et=9999999&sc=13109&shkr1=03&ar=030&bs=040&ct=9999999&shkr3=03&shkr2=03&srch_navi=1&mb=0&shkr4=03&cb=0.0',
    # 他のURLを追加する
]

# 物件情報を格納するためのリスト
properties_list = []

# 空のデータフレームを作成
df = pd.DataFrame()

# URLリストからURLを取得し、スクレイピングを実行
for url in url_list:
    # requestsでURLからデータを取得
    response = requests.get(url)
    response.encoding = response.apparent_encoding

    # BeautifulSoupオブジェクトの生成
    soup = BeautifulSoup(response.text, 'html.parser')

    # 物件情報が含まれる要素をすべて取得
    properties = soup.find_all('div', class_='property')

    # 物件情報の抽出
    for prop in properties:
        # 物件名が記載されているclassを選択
        title = prop.find('h2', class_='property_inner-title').text.strip()
        property_link = prop.find('a', class_='js-cassetLinkHref')['href']

        # 取り扱い店舗が記載されているclassを選択
        property_stores = prop.find('a', class_='js-noCassetteLink').text.strip()
        property_stores_link = prop.find('a', class_='js-noCassetteLink')['href']

        # 住所・アクセス経路・賃料・管理費・間取り・専有面積・向き・築年数・マンションかアパート・敷金・礼金が記載されているtdタグを選択
        detailbox = prop.find('div', class_='detailbox')
        if detailbox:

            # アクセス経路が記載されているtdタグを選択し、改行文字で分割して必要な部分を取得
            access_element = prop.find('div', class_='detailnote-box').text.strip()

            access_elements = access_element.split('\n')
            access_1 = access_elements[0].strip() if len(access_elements) > 0 else None
            access_2 = access_elements[1].strip() if len(access_elements) > 1 else None
            access_3 = access_elements[2].strip() if len(access_elements) > 2 else None

            # 賃料・管理費が記載されているtdタグを選択し、改行文字で分割して必要な部分を取得
            fee_element = detailbox.find_all('td', class_='detailbox-property-col')[0].text.strip()
            rent_price = fee_element.split('\n')[0].strip()
            management_fee =  fee_element.split('\n')[1].strip()

            # 敷金・礼金が記載されているtdタグを選択し、改行文字で分割して必要な部分を取得
            security_deposit_element = detailbox.find_all('td', class_='detailbox-property-col')[1].text.strip()
            security_deposit = security_deposit_element.split('\n')[0].strip()
            key_money = security_deposit_element.split('\n')[1].strip()

            # 間取り・専有面積・向きが記載されているtdタグを選択し、改行文字で分割して必要な部分を取得
            house_layout_element = detailbox.find_all('td', class_='detailbox-property-col')[2].text.strip()
            house_layout =  house_layout_element.split('\n')[0].strip()
            exclusive_area =  house_layout_element.split('\n')[2].strip()
            direction =  house_layout_element.split('\n')[4].strip()

            # 築年数とマンションかアパートが記載されているtdタグを選択し、改行文字で分割して必要な部分を取得
            building_type_element = detailbox.find_all('td', class_='detailbox-property-col')[3].text.strip()
            building_type =  building_type_element.split('\n')[0].strip()
            building_age = building_type_element.split('\n')[2].strip()

            # 住所が記載されているtdタグを正確に選択
            address = detailbox.find_all('td', class_='detailbox-property-col')[4].text.strip()

        # データリストに情報を追加
        properties_list.append({
            '物件名': title,
            '物件詳細URL': "https://suumo.jp"+property_link,
            'アドレス': address,
            'アクセス1': access_1,
            'アクセス2': access_2,
            'アクセス3': access_3,
            '築年数': building_age,
            '家賃': rent_price,
            '管理費': management_fee,
            '間取り': house_layout,
            '専有面積': exclusive_area,        
            '向き': direction,
            'タイプ': building_type,
            '敷金': security_deposit,
            '礼金': key_money,
            '取り扱い店舗': property_stores,
            '取り扱い店舗URL': "https://suumo.jp"+property_stores_link
        })

# データフレームの作成
df = pd.DataFrame(properties_list)

# 区のカラムを作成
df['区'] = df["アドレス"].apply(lambda x : x[x.find("都")+1:x.find("区")+1])

def change_fee(x):
    if ('万円' not in x) :
        return np.nan
    else:
        return float(x.split('万円')[0])

df['家賃'] = df['家賃'].apply(change_fee)

#DBファイルとして保存する関数
def save_to_database(quotes, db_name=None):
    if db_name is None:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = f'Property_data_{date_str}.db'
    try:
        df = pd.DataFrame(quotes)
        conn = sqlite3.connect(db_name)
        
        # テーブルが存在しない場合は作成する
        conn.execute('''CREATE TABLE IF NOT EXISTS Property_data
                        ({})'''.format(', '.join([f"{col} TEXT" for col in df.columns])))
        
        df.to_sql('Property_data', conn, if_exists='append', index=False)
        conn.close()
        logging.info(f"Data successfully saved to {db_name}")
    except Exception as e:
        logging.error(f"Error saving data to database: {e}")

# データベース名を指定
db_name = 'estate_list2.db'  # ここに実際のデータベースファイル名を入力してください

save_to_database(df, db_name)