import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import geocoder
import folium
import time
import requests
import urllib
import re
import sqlite3
from function.googlemap_api import get_lat_lon_google_map_api

# 物件データの読み込み
def estate_data(db_file_name='./scraping/estate_list2.db'):
    try:
        with sqlite3.connect(db_file_name) as conn:
            # SQLクエリを作成
            df = pd.read_sql('SELECT * FROM Property_data', conn)
            return df

    except Exception as e:
        st.error(f"データベースエラー: {e}")
        return pd.DataFrame()

# スターバックスのデータベースを読み込む関数
def load_starbucks_data(db_path, table_name):
    with sqlite3.connect(db_path) as conn:
        query = "SELECT store_name, address FROM quotes"
        return pd.read_sql_query(query, conn)

# スターバックスの店舗データを読み込む
def load_starbucks_df(area):
    db_path ='scraping/starbucks_list2.db'
    table_name ='quotes'
    starbucks_df = load_starbucks_data(db_path, table_name)

    # 区のカラムを作成
    starbucks_df['区'] = starbucks_df["address"].apply(lambda x: re.sub(r'\s', '', x[x.find("都")+1:x.find("区")+1]))
    # カラム名の住所をaddressにのみ変更
    starbucks_df = starbucks_df.rename(columns={'address': 'アドレス'})
    starbucks_df = starbucks_df.rename(columns={'store_name': '名称'})

    # 住所の正規化
    starbucks_df = normalize_address_in_df(starbucks_df, 'アドレス')

    # スターバックスの区別のデータを取得
    starbucks_filtered_df = starbucks_df[starbucks_df['区'] == area]

    # アドレスのデータを使って緯度経度のカラムデータを追加
    starbucks_filtered_df = preprocess_dataframe_tude(starbucks_filtered_df)

    return starbucks_filtered_df

# 地図上以外の物件も表示するボタンの状態を切り替える関数
def toggle_show_all():
    st.session_state['show_all'] = not st.session_state['show_all']


# HTML形式のハイパーリンクを生成する
def make_clickable(url, name):
    return f'<a target="_blank" href="{url}">{name}</a>'

# データフレームの前処理を行う関数
def preprocess_dataframe(df):
    # '家賃' 列を浮動小数点数に変換し、NaN値を取り除く
    df['家賃'] = pd.to_numeric(df['家賃'], errors='coerce')
    df = df.dropna(subset=['家賃'])
    return df

# 住所を正規化する関数
def normalize_address(address):
    # 全角数字と全角ハイフンを半角に変換
    address = address.translate(str.maketrans('０１２３４５６７８９－', '0123456789-'))
    
    # 不要な空白を削除
    address = re.sub(r'\s+', '', address)
    
    # 住所の形式を統一（例: "東京都渋谷区桜丘町1-2" -> "東京都 渋谷区 桜丘町 1-2"）
    # この例ではシンプルにスペースで区切っていますが、必要に応じて詳細な処理を追加できます
    address = re.sub(r'(\d+)-(\d+)', r'\1-\2', address)
    
    return address

# データフレームの指定された列を正規化する関数
def normalize_address_in_df(df, address_column):
    # データフレームの指定された住所列を正規化
    df[address_column] = df[address_column].apply(normalize_address)

    return df

# データフレームの前処理を行う関数（緯度経度取得用）
def preprocess_dataframe_tude(df):
    """
    アドレス列を基に緯度と経度の列を追加して、与えられたデータフレームを前処理します。
    """
    # 緯度・経度を取得
    # st.session_search_methodの値に応じて、緯度経度を取得する関数を変更
    if st.session_state.get('search_method', 'sokuchi') == 'sokuchi':
        df['latitude'], df['longitude'] = zip(*df['アドレス'].apply(get_lat_lon_sokuchi))
    elif st.session_state.get('search_method', 'sokuchi') == 'GeoPy':
        df['latitude'], df['longitude'] = zip(*df['アドレス'].apply(get_lat_lon))
    elif st.session_state.get('search_method', 'sokuchi') == 'geocoder':
        df['latitude'], df['longitude'] = zip(*df['アドレス'].apply(get_lat_lon_geocoder))
    else:
        df['latitude'], df['longitude'] = zip(*df['アドレス'].apply(get_lat_lon_google_map_api))

    # 'latitude' と 'longitude' 列を数値型に変換し、NaN値を含む行を削除
    df.loc[:, 'latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df.loc[:, 'longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    time.sleep(1)  # 連続リクエストを避けるために1秒待つ

    return df

# GeoPyを使用して緯度経度を取得する関数
def get_lat_lon(address):
    """
    アドレスから緯度経度を取得する関数
    アドレスが見つからない場合はNone, Noneを返す
    """
    try:
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            return (None, None)
    except GeocoderTimedOut:
        return (None, None)

# geocoderを使用して緯度経度を取得する関数
def get_lat_lon_geocoder(address):
    """
    アドレスから緯度経度を取得する関数
    アドレスが見つからない場合はNone, Noneを返す
    """
    try:
        g = geocoder.osm(address)
        if g.ok:
            return g.lat, g.lng
        else:
            return None, None
    except:
        return None, None

def get_lat_lon_sokuchi(address):
    """
    アドレスから緯度経度を取得する関数
    アドレスには住所文字列を渡す
    緯度経度が取得できない場合はNone, Noneを返す
    """
    base_url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="
    quoted_address = urllib.parse.quote(address)
    url = base_url + quoted_address
    
    try:
        response = requests.get(url)
        data = response.json()
        if data:
            coords = data[0]["geometry"]["coordinates"]
            return coords[1], coords[0]  # 緯度、経度の順番に注意
        else:
            return None, None
    except:
        return None, None



# 地図を作成し、マーカーを追加する関数
def create_map(filtered_df,starbucks_df=None):
    # 地図の初期設定
    map_center = [filtered_df['latitude'].mean(), filtered_df['longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=12)

    # マーカーを追加
    for idx, row in filtered_df.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
            # ポップアップに表示するHTMLコンテンツを作成
            popup_html = f"""
            <b>名称:</b> {row['物件名']}<br>
            <b>アドレス:</b> {row['アドレス']}<br>
            <b>家賃:</b> {row['家賃']}万円<br>
            <b>間取り:</b> {row['間取り']}<br>
            <a href="{row['物件詳細URL']}" target="_blank">物件詳細</a>
            """
            # HTMLをポップアップに設定
            popup = folium.Popup(popup_html, max_width=400)
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=popup
            ).add_to(m)
    return m

# 地図にユーザーの職場をマップに追加する関数
def add_user_to_map(m, user_df):
    for idx, row in user_df.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
            popup_html = f"""
            <b>ユーザー:</b> {row['名前']}<br>
            <b>住所:</b> {row['アドレス']}<br>
            """            

            # ユーザーのマーカーを追加
            popup = folium.Popup(popup_html, max_width=400)
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=popup,
                icon=folium.Icon(color='blue', icon='user', prefix='fa')
            ).add_to(m)
    return m

# 地図にユーザーとパートナーの職場を追加する関数
def add_partner_to_map(m, partner_df):
    for idx, row in partner_df.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
            popup_html = f"""
            <b>パートナー:</b> {row['名前']}<br>
            <b>住所:</b> {row['アドレス']}<br>
            """            

            # パートナーのマーカーを追加
            popup = folium.Popup(popup_html, max_width=400)
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=popup,
                icon=folium.Icon(color='red', icon='heart', prefix='fa')
            ).add_to(m)
    return m


# 地図にスターバックスのマーカーを追加する関数
def add_starbucks_to_map(m, starbucks_df):
    
    for idx, row in starbucks_df.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
            popup_html = f"""
            <b>店舗名:</b> {row['名称']}<br>
            <b>住所:</b> {row['アドレス']}<br>
            """
            popup = folium.Popup(popup_html, max_width=400)
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=popup,
                icon=folium.Icon(color='green', icon='coffee', prefix='fa')
            ).add_to(m)
    return m

# 検索結果を表示する関数
def display_search_results(filtered_df):
    # 物件番号を含む新しい列を作成
    filtered_df['物件番号'] = range(1, len(filtered_df) + 1)
    #filtered_df['物件詳細URL'] = filtered_df['物件詳細URL'].apply(lambda x: make_clickable(x, "リンク"))
    display_columns = ['物件番号', '物件名', 'アドレス', '家賃', '間取り', '物件詳細URL']
    filtered_df_display = filtered_df[display_columns]
    st.markdown(filtered_df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

# mapのオプションを表示する関数
def display_map_options(df):
    # 番号を含む新しい列を作成
    df['番号'] = range(1, len(df) + 1)
    display_columns = ['番号', '名称']
    df_display = df[display_columns]
    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

# SQLiteデータベースからキーワードに基づいて物件データを検索する関数
def search_estate_from_db(keyword):
    try:
        with sqlite3.connect(db_file_name='./scraping/estate_list.db') as conn:
            # SQLクエリで複数のカラムを検索
            query = """
                SELECT 名称, アドレス, 階数, 家賃, 間取り, 物件詳細URL
                FROM Property_data
                WHERE 名称 LIKE ? OR アドレス LIKE ?
            """
            # キーワードをパーセント記号で囲んで部分一致検索を可能にする
            params = ('%' + keyword + '%', '%' + keyword + '%')

            filtered_df = pd.read_sql_query(query, conn, params=params)
            return filtered_df
        
    except Exception as e:
        st.error(f"データベースエラー: {e}")
        return pd.DataFrame() # エラーが発生した場合は空のDataFrameを返す

def filter_estate_data(area, type_options, price_min, price_max, db_file_name='./scraping/estate_list2.db'):
    try:
        with sqlite3.connect(db_file_name) as conn:
            # SQLクエリを作成
            query = """
            SELECT *
            FROM Property_data
            WHERE 区 = ?
            AND 間取り IN ({})
            AND 家賃 BETWEEN ? AND ?
            """.format(','.join('?' * len(type_options)))

            # クエリのパラメータを設定
            params = [area] + type_options + [price_min, price_max]

            # SQLクエリを実行してフィルタリングされたデータを取得
            filtered_df = pd.read_sql_query(query, conn, params=params)
            # フィルタリングされたデータフレームの件数を取得
            filtered_count = len(filtered_df)
            return filtered_df, filtered_count
    except Exception as e:
        st.error(f"データベースエラー: {e}")
        return pd.DataFrame(), 0
    