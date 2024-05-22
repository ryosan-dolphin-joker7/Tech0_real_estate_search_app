#https://note.com/tnzk_k/n/n8d33b8bc1dd9
import streamlit as st
import googlemaps #pip install googlemaps

import os
from dotenv import load_dotenv

# Set your Google Maps API key
# Load API key from .env file
load_dotenv()
MAPS_API_KEY = os.getenv("MAPS_API_KEY")

if not MAPS_API_KEY:
    st.error("Google Maps APIキーが設定されていません。")
    st.stop()

#print(f"Google Maps APIキー: {MAPS_API_KEY}")  # デバッグ用

def get_lat_lon_google_map_api(address):
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

