#https://note.com/tnzk_k/n/n8d33b8bc1dd9
import streamlit as st
import folium #pip install folium
from streamlit_folium import st_folium
from pprint import pprint 
import googlemaps #pip install googlemaps
import pandas as pd
from tqdm import tqdm #pip install tqdm
import os
from dotenv import load_dotenv

# Set your Google Maps API key
# Load API key from .env file
load_dotenv()
MAPS_API_KEY = os.getenv("MAPS_API_KEY")

if not MAPS_API_KEY:
    st.error("Google Maps APIキーが設定されていません。")
    st.stop()

print(f"Google Maps APIキー: {MAPS_API_KEY}")  # デバッグ用


def geocode(address):
    try:
        gmaps = googlemaps.Client(key=MAPS_API_KEY)
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            lat = geocode_result[0]['geometry']['location']['lat']
            lng = geocode_result[0]['geometry']['location']['lng']
            return lat, lng
        else:
            return None, None
    except Exception as e:
        print(f"Error geocording {address}: {e}")
        return None, None

filepath = "address.csv"
df = pd.read_csv(filepath)

geocode_result = []
for ad in tqdm(df["address"]):
    lat, lng = geocode(ad)
    if lat is not None and lng is not None:
        geocode_result.append((lat, lng))
    else:
        print(f"Geocode failed for address: {ad}")
        geocode_result.append((None, None))

_df = pd.DataFrame(geocode_result, columns=['latitude', 'longitude'])
df = df.join(_df)
df.dropna(subset=['latitude', 'longitude'], inplace=True)

if df.empty:
    st.error("全てのジオコード取得に失敗しました。APIキーを確認してください。")
    st.stop()

df.to_csv("address_with_geocode.csv", index=False)

# Calculate the center coordinates of the locations
center_lat = df['latitude'].mean()
center_lng = df['longitude'].mean()

# Create a map using folium with the center coordinates
m = folium.Map(location=[center_lat, center_lng], zoom_start=12)

# Add markers to the map
for index, row in df.iterrows():
    lat = row['latitude']
    lng = row['longitude']
    address = row['address']
    folium.Marker([lat, lng], popup=address, tooltip=folium.Tooltip(address, direction='horizontal')).add_to(m)

# Display the map using streamlit
st.write("ファイルに記載された住所を地図に表示")
# Display the map using streamlit
st_folium(m)