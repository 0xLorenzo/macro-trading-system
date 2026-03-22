import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Macro Trading System", layout="wide")

st.title("🌍 AI Macro Trading System")

# ===== DATA =====
@st.cache_data(ttl=3600)
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    return requests.get(url).json()["bitcoin"]["usd"]

btc_price = get_btc_price()
oil_price = 90
dxy = 102
btc_vol = 60

rate = st.selectbox("Fed Policy", ["Hawkish", "Neutral", "Dovish"])

# ===== MODEL =====
def model(oil, dxy, fed, vol):
    gold, stocks, btc, cash = 25, 40, 20, 15

    if oil > 110:
        gold += 10; stocks -= 10
    if dxy > 105:
        btc -= 5; cash += 5
    if fed == "Dovish":
        stocks += 5; btc += 5; cash -= 10
    if vol > 80:
        btc += 5; cash -= 5

    total = gold+stocks+btc+cash
    return {
        "Gold": gold/total*100,
        "Stocks": stocks/total*100,
        "BTC": btc/total*100,
        "Cash": cash/total*100
    }

alloc = model(oil_price, dxy, rate, btc_vol)

# ===== UI =====
st.subheader("📊 Allocation")
df = pd.DataFrame(alloc.items(), columns=["Asset","%"])
st.bar_chart(df.set_index("Asset"))

st.subheader("📡 Market")
st.write(f"BTC Price: ${btc_price}")

st.subheader("🧠 Strategy")
if oil_price > 110:
    st.write("⚠️ Increase Gold")
if dxy > 105:
    st.write("💵 Strong USD")
if rate == "Dovish":
    st.write("📈 Bullish risk assets")
