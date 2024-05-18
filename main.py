import os
import streamlit as st
import pandas as pd
import numpy as np
from dotenv import load_dotenv


from streamlit_folium import folium_static
from function.db_search_function import preprocess_dataframe,preprocess_dataframe_tude, make_clickable, create_map
from function.create_df import create_sample_df

# 環境変数の読み込み
load_dotenv()

# 環境変数から認証情報を取得
#SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
#PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
#SP_SHEET     = 'tech0_01' # sheet名

df = create_sample_df()
df = preprocess_dataframe_tude(df)

# セッション状態の初期化
if 'show_all' not in st.session_state:
    st.session_state['show_all'] = False  # 初期状態は地図上の物件のみを表示


# 検索結果を表示する関数
def display_search_results(filtered_df):
    # 物件番号を含む新しい列を作成
    filtered_df['物件番号'] = range(1, len(filtered_df) + 1)
    filtered_df['物件詳細URL'] = filtered_df['物件詳細URL'].apply(lambda x: make_clickable(x, "リンク"))
    display_columns = ['物件番号', '名称', 'アドレス', '階数', '家賃', '間取り', '物件詳細URL']
    filtered_df_display = filtered_df[display_columns]
    st.markdown(filtered_df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

# メインのアプリケーション
def main():
    df = create_sample_df()
    df = preprocess_dataframe(df)
    df = preprocess_dataframe_tude(df)

    # StreamlitのUI要素（スライダー、ボタンなど）の各表示設定
    st.title('賃貸物件情報の可視化')

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


    # フィルタリング/ フィルタリングされたデータフレームの件数を取得
    filtered_df = df[(df['区'].isin([area])) & (df['間取り'].isin(type_options))]
    filtered_df = filtered_df[(filtered_df['家賃'] >= price_min) & (filtered_df['家賃'] <= price_max)]
    filtered_count = len(filtered_df)

    
    # 'latitude' と 'longitude' 列を数値型に変換し、NaN値を含む行を削除
    filtered_df['latitude'] = pd.to_numeric(filtered_df['latitude'], errors='coerce')
    filtered_df['longitude'] = pd.to_numeric(filtered_df['longitude'], errors='coerce')
    filtered_df2 = filtered_df.dropna(subset=['latitude', 'longitude'])
    

    # 検索ボタン / # フィルタリングされたデータフレームの件数を表示
    col2_1, col2_2 = st.columns([1, 2])

    with col2_2:
        st.write(f"物件検索数: {filtered_count}件 / 全{len(df)}件")

    # 検索ボタン
    if col2_1.button('検索＆更新', key='search_button'):
        # 検索ボタンが押された場合、セッションステートに結果を保存
        st.session_state['filtered_df'] = filtered_df
        st.session_state['filtered_df2'] = filtered_df2
        st.session_state['search_clicked'] = True

    # Streamlitに地図を表示
    if st.session_state.get('search_clicked', False):
        m = create_map(st.session_state.get('filtered_df2', filtered_df2))
        folium_static(m)

    # 地図の下にラジオボタンを配置し、選択したオプションに応じて表示を切り替える
    show_all_option = st.radio(
        "表示オプションを選択してください:",
        ('地図上の検索物件のみ', 'すべての検索物件'),
        index=0 if not st.session_state.get('show_all', False) else 1,
        key='show_all_option'
    )

    # ラジオボタンの選択に応じてセッションステートを更新
    st.session_state['show_all'] = (show_all_option == 'すべての検索物件')

    # 検索結果の表示
    if st.session_state.get('search_clicked', False):
        if st.session_state['show_all']:
            display_search_results(st.session_state.get('filtered_df', filtered_df))  # 全データ
        else:
            display_search_results(st.session_state.get('filtered_df2', filtered_df2))  # 地図上の物件のみ


# アプリケーションの実行
if __name__ == "__main__":
    if 'search_clicked' not in st.session_state:
        st.session_state['search_clicked'] = False
    if 'show_all' not in st.session_state:
        st.session_state['show_all'] = False
    main()