import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from streamlit_folium import folium_static
import re

# 他のPythonファイルから関数をインポート
from function.create_df import create_sample_df
from function.db_search_function import normalize_address_in_df
from function.db_search_function import preprocess_dataframe,preprocess_dataframe_tude
from function.db_search_function import create_map, display_search_results, add_starbucks_to_map
from function.db_search_function import display_search_results
from function.db_search_function import filter_estate_data
from function.db_search_function import load_starbucks_data

# 環境変数の読み込み
load_dotenv() #今は使わない

# 環境変数から認証情報を取得
#SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
#PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
#SP_SHEET     = 'tech0_01' # sheet名


# セッション状態の初期化
if 'show_all' not in st.session_state:
    st.session_state['show_all'] = False  # 初期状態は地図上の物件のみを表示

# サイドバーに緯度経度の検索方法を選択するセレクトボックスを追加
st.session_search_method = st.sidebar.selectbox(
    '緯度経度検索方法:',
    ('Google Maps API', 'Geopy', 'geocoder', '国土地理院地理院地図API'),
)

# 物件データの読み込み
def load_estate_data():
    # データフレームの読み込み
    df = create_sample_df()

    # 住所の正規化
    df = normalize_address_in_df(df, 'アドレス')

    # データフレームの前処理をする関数を呼び出し
    df = preprocess_dataframe(df)

    return df

# スターバックスの店舗データを読み込む
def load_starbucks_df(area):
    db_path ='scraping/starbucks_list2.db'
    table_name ='quotes'
    starbucks_df = load_starbucks_data(db_path, table_name)

    # 区のカラムを作成
    starbucks_df['区'] = starbucks_df["address"].apply(lambda x: re.sub(r'\s', '', x[x.find("都")+1:x.find("区")+1]))
    # カラム名の住所をaddressにのみ変更
    starbucks_df = starbucks_df.rename(columns={'address': 'アドレス'})

    # 住所の正規化
    starbucks_df = normalize_address_in_df(starbucks_df, 'アドレス')

    # スターバックスの区別のデータを取得
    starbucks_filtered_df = starbucks_df[starbucks_df['区'] == area]

    # アドレスのデータを使って緯度経度のカラムデータを追加
    starbucks_filtered_df = preprocess_dataframe_tude(starbucks_filtered_df)

    return starbucks_filtered_df

# メインのアプリケーション
def main():
    # 物件データの読み込み
    df = load_estate_data()

    # StreamlitのUI要素（スライダー、ボタンなど）の各表示設定
    st.title('賃貸物件情報の検索')

    # エリアと家賃フィルタバーを1:2の割合で分割
    col1, col2 = st.columns([1, 2])

    with col1:
        # エリア選択
        area = st.radio('■ エリア選択', df['区'].unique())

    with col2:
        # 家賃範囲選択のスライダーをfloat型で設定し、小数点第一位まで表示
        price_min, price_max = st.slider(
            '■ 家賃範囲 (万円)', 
            min_value=float(1), 
            max_value=float(df['家賃'].max()),
            value=(float(df['家賃'].min()), float(df['家賃'].max())),
            step=0.1,  # ステップサイズを0.1に設定
            format='%.1f'
        )

    with col2:
    # 間取り選択のデフォルト値をすべてに設定
        type_options = st.multiselect('■ 間取り選択', df['間取り'].unique(), default=df['間取り'].unique())


    # フィルタリングされたデータフレームとデータ件数を取得
    filtered_df = df[(df['区'].isin([area])) & (df['間取り'].isin(type_options))]
    filtered_df = filtered_df[(filtered_df['家賃'] >= price_min) & (filtered_df['家賃'] <= price_max)]
    filtered_count = len(filtered_df)

    # アドレスのデータを使って緯度経度のカラムデータを追加
    filtered_df = preprocess_dataframe_tude(filtered_df)
    # 緯度・経度が取得できない行を削除
    filtered_df2 = filtered_df.dropna(subset=['latitude', 'longitude'])

    # デバッグ用の出力
    #st.write("df:", df)
    #st.write("filtered_df:", filtered_df)
    #st.write("starbucks_df:", starbucks_df)
    #st.write("starbucks_filtered_df:", starbucks_filtered_df)

    # 検索ボタン / # フィルタリングされたデータフレームの件数を表示
    col2_1, col2_2 = st.columns([1, 2])

    # SQLiteでのフィルタリング条件と検索結果を表示
    filtered_df3, filtered_count3 = filter_estate_data(area, type_options, price_min, price_max)

    with col2_2:
        st.write(f"物件検索数: {filtered_count}件 / 全{len(df)}件")

    # 検索ボタン
    if col2_1.button('検索＆更新', key='search_button'):
        # 検索ボタンが押された場合、セッションステートに結果を保存
        st.session_state['filtered_df'] = filtered_df
        st.session_state['filtered_df2'] = filtered_df2
        st.session_state['search_clicked'] = True

    # 検索結果の表示
    # 検索ボタンが押された場合のみ、検索結果を表示
    if st.session_state.get('search_clicked', False):
        display_search_results(st.session_state.get('filtered_df', filtered_df))  # 全データ

    # 地図の表示ボタン
    st.header("地図の表示")
    # 間取り選択のデフォルト値をすべてに設定
    map_options = st.multiselect('■ 表示ピン選択', ['スタバ','幼稚園'])

    if st.button('地図の表示', key='map_button'):
        # 検索ボタンが押された場合、セッションステートに結果を保存
        st.session_state['map_clicked'] = True

    # Streamlitに地図を表示
    # 地図の表示ボタンが押された場合のみ、地図を表示
    if st.session_state.get('map_clicked', False):
        m = create_map(st.session_state.get('filtered_df2', filtered_df2))

        if 'スタバ' in map_options:
            # スターバックスの区別のデータを取得
            starbucks_filtered_df = load_starbucks_df(area)
            m = add_starbucks_to_map(m, starbucks_filtered_df)  # スターバックスの店舗を追加
            folium_static(m)

    # 地図の下にラジオボタンを配置し、選択したオプションに応じて表示を切り替える
    show_all_option = st.radio(
        "表示オプションを選択してください:",
        ('地図上の検索物件のみ', 'すべての検索物件'),
        index=0 if not st.session_state.get('show_all', False) else 1,
        key='show_all_option'
    )

    # 地図ボタンが押された場合のみ、検索結果を表示
    if st.session_state.get('map_clicked', False):
        if st.session_state['show_all']:
            display_search_results(st.session_state.get('filtered_df', filtered_df))  # 全データ
        else:
            display_search_results(st.session_state.get('filtered_df2', filtered_df2))  # 地図上の物件のみ
    # ラジオボタンの選択に応じてセッションステートを更新
    st.session_state['show_all'] = (show_all_option == 'すべての検索物件')

    # 物件の選択
    st.header("物件の選択")

    # チェックボックスを表示し、選択された行を保存するリストを初期化
    selected_rows = []

    # 各行にチェックボックスを追加
    for index, row in filtered_df2.iterrows():
        if st.checkbox(f"行 {index} - {row['名称']}"):
            selected_rows.append(index)
    
    # 選択された行のデータを取得
    selected_data = filtered_df2.loc[selected_rows]

    # 選択された行のデータを表示
    st.write("選択された行のデータ:")
    st.dataframe(selected_data)

# アプリケーションの実行
if __name__ == "__main__":
    if 'search_clicked' not in st.session_state:
        st.session_state['search_clicked'] = False
    if 'show_all' not in st.session_state:
        st.session_state['show_all'] = False
    main()