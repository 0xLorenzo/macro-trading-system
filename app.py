import streamlit as st
import pandas as pd
import requests
import datetime

st.set_page_config(page_title="宏观交易系统V5", layout="wide")

st.markdown(
    """
    <h1 style='text-align:center;color:#1E3A8A;'>🌍 AI 宏观交易策略系统 V5</h1>
    <p style='text-align:center;color:#555;font-size:14px;'>
    根据原油、美元指数、BTC波动率和美联储政策，自动推荐资产配置比例和策略提示，并提供历史数据可视化和下载功能。
    </p>
    """,
    unsafe_allow_html=True
)

# ===== 侧边栏 =====
with st.sidebar:
    st.header("📥 输入参数")
    oil_price = st.slider("原油价格 (USD)", 50, 150, 90)
    dxy = st.slider("美元指数 (DXY)", 90, 120, 102)
    btc_vol = st.slider("BTC波动率 (%)", 20, 120, 60)
    rate = st.selectbox("美联储政策", ["鹰派", "中性", "鸽派"])

    st.markdown("---")
    st.write("📌 调整各项输入后，主界面将实时更新资产配置和策略提示。")
    st.write(f"更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ===== 获取 BTC 实时价格 =====
@st.cache_data(ttl=3600)
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    try:
        return requests.get(url, timeout=5).json()["bitcoin"]["usd"]
    except:
        return None

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
        "黄金": round(gold / total * 100, 1),
        "美股": round(stocks / total * 100, 1),
        "BTC": round(btc / total * 100, 1),
        "现金": round(cash / total * 100, 1)
    }

alloc = model(oil_price, dxy, rate, btc_vol)

# ===== 历史数据模拟 =====
history_data = pd.DataFrame({
    '日期': pd.date_range(end=datetime.datetime.today(), periods=30),
    '黄金': [alloc['黄金']+i*0.1 for i in range(30)],
    '美股': [alloc['美股']+i*0.05 for i in range(30)],
    'BTC': [alloc['BTC']+i*0.2 for i in range(30)],
    '现金': [alloc['现金']-i*0.1 for i in range(30)]
})

# ===== 主界面显示 =====
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 资产配置建议")
    df = pd.DataFrame(alloc.items(), columns=["资产", "%"])
    st.bar_chart(df.set_index("资产"))
    st.table(df)

with col2:
    st.subheader("📡 当前市场信息")
    st.write(f"**BTC价格:** ${btc_price if btc_price else '获取失败'}")
    st.write(f"**原油价格:** ${oil_price}")
    st.write(f"**美元指数:** {dxy}")
    st.write(f"**BTC波动率:** {btc_vol}%")
    st.write(f"**美联储政策:** {rate}")

# ===== 策略提示 =====
st.markdown("---")
st.subheader("🧠 投资策略提示与解释")

def add_strategy(title, message, explanation, color):
    st.markdown(f"<span style='color:{color};font-weight:bold;'>{title}</span>: {message}", unsafe_allow_html=True)
    with st.expander("解释与提醒"):
        st.write(explanation)

# 战争风险
if oil_price > 110:
    add_strategy("🔴 战争风险高", "建议增持黄金，降低高风险资产", "原油价格过高通常意味着全球能源供应紧张或局势动荡，黄金作为避险资产价值上升，风险资产承压。", "red")
elif oil_price < 80:
    add_strategy("🟢 战争风险低", "当前能源供应较稳定", "原油价格较低，说明供应充足，风险资产相对安全，黄金不必额外增加仓位。", "green")
else:
    add_strategy("🟡 战争风险中性", "能源风险一般，保持均衡配置", "原油价格中性，说明能源市场稳定，资产配置保持均衡即可。", "orange")

# 美元影响
if dxy > 105:
    add_strategy("🔴 美元强势", "风险资产承压", "美元升值导致全球资本流回美国，风险资产承压，适合增加现金或防守资产。", "red")
elif dxy < 98:
    add_strategy("🟢 美元偏弱", "利好风险资产", "美元疲软，全球流动性宽松，有利于股票和加密资产，风险资产可以适度加仓。", "green")
else:
    add_strategy("🟡 美元中性", "风险资产波动正常", "美元指数中性，对市场影响有限，资产配置保持均衡即可。", "orange")

# 利率政策
if rate == "鸽派":
    add_strategy("📈 鸽派政策", "流动性宽松，利好BTC和科技股", "鸽派政策通常意味着低利率和宽松流动性，有助于提升风险资产估值，适合加仓科技股和加密资产。", "green")
elif rate == "鹰派":
    add_strategy("📉 鹰派政策", "流动性收紧，抑制风险资产", "鹰派政策意味着紧缩流动性，高利率环境下风险资产承压，适合减仓高波动资产。", "red")
else:
    add_strategy("ℹ️ 政策中性", "保持均衡配置", "中性政策下，流动性影响较小，资产配置保持均衡即可。", "orange")

# BTC波动
if btc_vol > 80:
    add_strategy("⚡ BTC高波动", "适合波段操作", "BTC波动大，短期价格可能大幅震荡，适合有经验的波段操作，注意控制仓位和止损。", "red")
elif btc_vol < 40:
    add_strategy("📌 BTC波动低", "适合持有", "波动率低，市场情绪稳定，可长期持有BTC，减少频繁交易。", "green")
else:
    add_strategy("ℹ️ BTC波动中等", "常规操作", "波动率中等，适合维持当前仓位，常规操作即可。", "orange")

# ===== 历史趋势图 =====
st.markdown("---")
st.subheader("📈 资产配置历史趋势")
st.line_chart(history_data.set_index('日期'))

# ===== 下载功能 =====
st.markdown("---")
st.subheader("💾 下载策略报告")
csv = history_data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="下载历史资产配置数据 (CSV)",
    data=csv,
    file_name='macro_trading_history.csv',
    mime='text/csv'
)

# ===== 总结说明 =====
with st.expander("📘 策略规则及风险说明"):
    st.write("""
    - 原油价格反映能源紧张和战争风险，价格高避险资产受益。
    - 美元指数高意味着全球资本回流美国，风险资产承压。
    - BTC波动率可作为市场情绪和短期波段交易参考。
    - 美联储政策影响流动性，鸽派利好风险资产，鹰派抑制。
    - 历史趋势图帮助参考过去30天的资产配置变化。
    - 下载功能可以导出数据用于外部分析。
    - 本系统仅提供策略参考，不构成投资建议，请自行评估风险。
    """)
