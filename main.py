import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from streamlit_folium import folium_static
import re

# 他のPythonファイルから関数をインポート
from function.create_df import create_sample_df
from function.db_search_function import normalize_address_in_df
from function.db_search_function import preprocess_dataframe,preprocess_dataframe_tude
from function.db_search_function import create_map, add_starbucks_to_map
from function.db_search_function import make_clickable
from function.db_search_function import display_search_results
from function.db_search_function import display_map_options
from function.db_search_function import filter_estate_data
from function.db_search_function import load_starbucks_df
from function.db_search_function import add_user_to_map
from function.db_search_function import add_partner_to_map
from function.db_search_function import estate_data

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
    #df = create_sample_df()
    df = estate_data()

    # 住所の正規化
    df = normalize_address_in_df(df, 'アドレス')

    # データフレームの前処理をする関数を呼び出し
    df = preprocess_dataframe(df)

    return df

user_df = pd.DataFrame()
partner_df = pd.DataFrame()

# メインのアプリケーション
def main():
    # 物件データを読み込んでいない場合に実施
    if 'df' not in st.session_state:
        # 物件データの読み込み
        st.session_state['df'] = load_estate_data()

    df = st.session_state['df']

    # StreamlitのUI要素（スライダー、ボタンなど）の各表示設定
    st.title('賃貸物件情報の検索アプリ：ホームクエスト')
    st.write('このアプリケーションは、賃貸物件情報を検索するためのものです。')

    st.header("ユーザー情報の入力")
    # エリアと家賃フィルタバーを1:2の割合で分割
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        # ユーザーとパートナーの職場を入力してもらう
        user_name = st.text_input('■ あなたの名前を入力してください', 'ユーザー名')
        user_workplace = st.text_input('■ あなたの職場の住所を入力してください', '東京都千代田区永田町１丁目７−１')
        user_like_madori = st.text_input('■ あなたの好きな間取りを入力してください', '2K')
        user_hope_fee = st.text_input('■ あなたの希望家賃を入力してください', '20')
        # ユーザー情報をデータフレームに追加
        user_df = pd.DataFrame({
            '名前': [user_name],
            'アドレス': [user_workplace],
            '間取り': [user_like_madori],
            '家賃': [user_hope_fee]
        })

    with col2_2:
        partner_name = st.text_input('■ パートナーの名前を入力してください', 'パートナー名')
        partner_workplace = st.text_input('■ パートナーの職場の住所を入力してください', '東京都中央区銀座1丁目12番4号')
        partner_like_madori = st.text_input('■ パートナーの好きな間取りを入力してください', '1LDK')
        partner_hope_fee = st.text_input('■ パートナーの希望家賃を入力してください', '15')
        # パートナー情報をデータフレームに追加
        partner_df = pd.DataFrame({
            '名前': [partner_name],
            'アドレス': [partner_workplace],
            '間取り': [partner_like_madori],
            '家賃': [partner_hope_fee]
        })
    # ユーザーとパートナーのデータフレームを結合する
    user_partner_df = pd.concat([user_df, partner_df], ignore_index=True)

    st.header("物件の検索条件")
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
            max_value=float(40),
            value=(float(user_partner_df['家賃'].min()), float(user_partner_df['家賃'].max())),
            step=0.1,  # ステップサイズを0.1に設定
            format='%.1f'
        )

    with col2:
    # 間取り選択のデフォルト値をすべてに設定
        type_options = st.multiselect('■ 間取り選択', df['間取り'].unique(), default=user_partner_df['間取り'].unique())

    # フィルタリングされたデータフレームとデータ件数を取得
    filtered_df = df[(df['区'].isin([area])) & (df['間取り'].isin(type_options))]
    filtered_df = filtered_df[(filtered_df['家賃'] >= price_min) & (filtered_df['家賃'] <= price_max)]
    filtered_count = len(filtered_df)

    # 物件詳細URLの列を作成
    filtered_df['物件詳細URL'] = filtered_df['物件詳細URL'].apply(lambda x: make_clickable(x, "リンク"))

    # アドレスのデータを使って緯度経度のカラムデータを追加
    filtered_df = preprocess_dataframe_tude(filtered_df)
    user_df = preprocess_dataframe_tude(user_df)
    partner_df = preprocess_dataframe_tude(partner_df)

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
    if col2_1.button('検索結果のリスト表示', key='search_button'):
        # 検索ボタンが押された場合、セッションステートに結果を保存
        st.session_state['filtered_df'] = filtered_df
        st.session_state['filtered_df2'] = filtered_df2
        #st.session_state['filtered_df3'] = filtered_df3
        st.session_state['search_clicked'] = True

    # 検索結果の表示
    # 検索ボタンが押された場合のみ、検索結果を表示
    if st.session_state.get('search_clicked', False):
        display_search_results(st.session_state.get('filtered_df', filtered_df))  # 全データ
        #display_search_results(st.session_state.get('filtered_df3', filtered_df3))

    # 地図の表示ボタン
    st.header("地図の表示")

    if st.button('地図の表示', key='map_button'):
        # 検索ボタンが押された場合、セッションステートに結果を保存
        st.session_state['map_clicked'] = True

    # Streamlitに地図を表示
    # 地図の表示ボタンが押された場合のみ、地図を表示
    if st.session_state.get('map_clicked', False):
        m = create_map(st.session_state.get('filtered_df2', filtered_df2))
        m = add_user_to_map(m, user_df)  # ユーザーの職場を追加
        m = add_partner_to_map(m, partner_df)  # パートナーの職場を追加
        folium_static(m)

    # 地図の表示ボタン
    st.header("追加オプションの地図表示")
    # 間取り選択のデフォルト値をすべてに設定
    map_options = st.multiselect('■ 表示ピン選択', ['スタバ','幼稚園'])

    if st.button('追加オプションの地図表示', key='map_options_button'):
        # 検索ボタンが押された場合、セッションステートに結果を保存
        st.session_state['map_options_clicked'] = True

    # 追加オプションを地図に表示
    # 地図の表示ボタンが押された場合のみ、地図を表示
    if st.session_state.get('map_options_clicked', False):

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
    if st.session_state.get('map_options_clicked', False):
        if st.session_state['show_all']:
            display_map_options(st.session_state.get('starbucks_filtered_df', starbucks_filtered_df))  # 全データ
        else:
            display_map_options(st.session_state.get('starbucks_filtered_df', starbucks_filtered_df))  # 地図上の物件のみ

    # ラジオボタンの選択に応じてセッションステートを更新
    st.session_state['show_all'] = (show_all_option == 'すべての検索物件')


    # 物件の選択
    st.header("物件の選択")

    # チェックボックスを表示し、選択された行を保存するリストを初期化
    selected_rows = []

    # 各行にチェックボックスを追加
    for index, row in filtered_df2.iterrows():
        if st.checkbox(f"行 {index} - {row['物件名']}"):
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