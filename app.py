import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="宏观交易系统", layout="wide")

st.title("🌍 AI 宏观交易系统")

# ===== 动态输入数据 =====
oil_price = st.slider("原油价格 (USD)", 50, 150, 90)
dxy = st.slider("美元指数 (DXY)", 90, 120, 102)
btc_vol = st.slider("BTC波动率 (%)", 20, 120, 60)
rate = st.selectbox("美联储政策", ["鹰派", "中性", "鸽派"])

# ===== 获取 BTC 价格 =====
@st.cache_data(ttl=3600)
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    return requests.get(url).json()["bitcoin"]["usd"]

btc_price = get_btc_price()

# ===== 模型计算 =====
def model(oil, dxy, fed, vol):
    gold, stocks, btc, cash = 25, 40, 20, 15

    if oil > 110:
        gold += 10
        stocks -= 10
    elif oil < 80:
        stocks += 5
        gold -= 5

    if dxy > 105:
        btc -= 5
        cash += 5
    elif dxy < 98:
        btc += 5
        cash -= 5

    if fed == "鸽派":
        stocks += 5
        btc += 5
        cash -= 10
    elif fed == "鹰派":
        stocks -= 5
        gold += 5

    if vol > 80:
        btc += 5
        cash -= 5

    total = gold + stocks + btc + cash
    return {
        "黄金": gold / total * 100,
        "美股": stocks / total * 100,
        "BTC": btc / total * 100,
        "现金": cash / total * 100
    }

alloc = model(oil_price, dxy, rate, btc_vol)

# ===== 资产配置界面 =====
st.subheader("📊 资产配置")
df = pd.DataFrame(alloc.items(), columns=["资产", "%"])
st.bar_chart(df.set_index("资产"))

# ===== 市场信息 =====
st.subheader("📡 市场信息")
st.write(f"BTC价格: ${btc_price}")
st.write(f"原油价格: ${oil_price}")
st.write(f"美元指数: {dxy}")
st.write(f"BTC波动率: {btc_vol}%")
st.write(f"美联储政策: {rate}")

# ===== 策略提示 =====
st.subheader("🧠 策略提示")

if oil_price > 110:
    st.write("⚠️ 战争风险高，建议增加黄金仓位")
elif oil_price < 80:
    st.write("✅ 战争风险低，黄金仓位可保持")
else:
    st.write("ℹ️ 战争风险中性，保持均衡配置")

if dxy > 105:
    st.write("💵 美元走强，风险资产承压")
elif dxy < 98:
    st.write("✅ 美元弱势，利好风险资产")
else:
    st.write("ℹ️ 美元中性，风险资产波动正常")

if rate == "鸽派":
    st.write("📈 流动性宽松，利好BTC和科技股")
elif rate == "鹰派":
    st.write("📉 流动性紧缩，压制风险资产")
else:
    st.write("ℹ️ 市场中性，保持均衡配置")

if btc_vol > 80:
    st.write("🔁 BTC高波动，适合波段操作")
elif btc_vol < 40:
    st.write("✅ BTC波动低，适合持有")
else:
    st.write("ℹ️ BTC波动中等，常规操作")
