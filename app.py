import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="宏观交易系统", layout="wide")

st.title("🌍 AI 宏观交易系统")

# ===== 数据获取 =====
@st.cache_data(ttl=3600)
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    return requests.get(url).json()["bitcoin"]["usd"]

btc_price = get_btc_price()
oil_price = 90
dxy = 102
btc_vol = 60

rate = st.selectbox("美联储政策", ["鹰派", "中性", "鸽派"])

# ===== 模型计算 =====
def model(oil, dxy, fed, vol):
    gold, stocks, btc, cash = 25, 40, 20, 15

    if oil > 110:
        gold += 10; stocks -= 10
    if dxy > 105:
        btc -= 5; cash += 5
    if fed == "鸽派":
        stocks += 5; btc += 5; cash -= 10
    if vol > 80:
        btc += 5; cash -= 5

    total = gold+stocks+btc+cash
    return {
        "黄金": gold/total*100,
        "美股": stocks/total*100,
        "BTC": btc/total*100,
        "现金": cash/total*100
    }

alloc = model(oil_price, dxy, rate, btc_vol)

# ===== 界面显示 =====
st.subheader("📊 资产配置")
df = pd.DataFrame(alloc.items(), columns=["资产", "%"])
st.bar_chart(df.set_index("资产"))

st.subheader("�
