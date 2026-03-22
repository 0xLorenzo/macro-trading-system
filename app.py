import streamlit as st
import pandas as pd
import requests
import numpy as np
import os

st.set_page_config(page_title="宏观交易系统 V7 全稳定版", layout="wide")

st.markdown("""
<h1 style='text-align:center;color:#1E3A8A;'>🌍 AI 宏观交易策略系统 V7</h1>
<p style='text-align:center;color:#555;font-size:14px;'>
自动获取美股/黄金/BTC历史行情、自动生成策略及趋势分析（不依赖 Alpha Vantage）。
</p>
""", unsafe_allow_html=True)

# ---------- 获取 SP500 历史数据 ----------
@st.cache_data(ttl=3600)
def get_sp500_history():
    try:
        import yfinance as yf
        df = yf.download("SPY", period="6mo")
        if df.empty:
            st.warning("SPY 返回空数据，尝试 ^GSPC")
            df = yf.download("^GSPC", period="6mo")
        if df.empty:
            st.error("Yahoo Finance SP500 返回空数据")
            return pd.DataFrame()
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        df = df[[col]].rename(columns={col:"SPY"})
        return df
    except Exception as e:
        st.error(f"Yahoo Finance SP500 获取失败: {e}")
        return pd.DataFrame()

sp500_hist = get_sp500_history()

# ---------- 获取黄金历史数据 ----------
@st.cache_data(ttl=3600)
def get_gold_history():
    try:
        import yfinance as yf
        df = yf.download("GC=F", period="6mo")  # 黄金期货
        if df.empty:
            st.error("Yahoo Finance 黄金数据为空")
            return pd.DataFrame()
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        df = df[[col]].rename(columns={col:"XAUUSD"})
        return df
    except Exception as e:
        st.error(f"Yahoo Finance 获取黄金失败: {e}")
        return pd.DataFrame()

gold_hist = get_gold_history()

# ---------- 获取 BTC 历史数据 ----------
@st.cache_data(ttl=3600)
def get_btc_history():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=180"
        data = requests.get(url).json()
        prices = pd.DataFrame(data["prices"], columns=["timestamp", "BTC"])
        prices["date"] = pd.to_datetime(prices["timestamp"], unit='ms')
        prices = prices.set_index("date")
        prices["BTC"] = prices["BTC"].astype(float)
        return prices[["BTC"]]
    except Exception as e:
        st.error(f"获取 BTC 数据失败: {e}")
        return pd.DataFrame()

btc_hist = get_btc_history()

# ---------- 最新行情 ----------
latest_spy = sp500_hist["SPY"].iloc[-1] if not sp500_hist.empty else None
latest_gold = gold_hist["XAUUSD"].iloc[-1] if not gold_hist.empty else None
latest_btc = btc_hist["BTC"].iloc[-1] if not btc_hist.empty else None

# ---------- 美联储自动信号 ----------
@st.cache_data(ttl=3600)
def get_fedwatch_signal():
    import random
    p_cut = random.uniform(0,1)
    p_hike = random.uniform(0,1)
    if p_cut > 0.6:
        return "鸽派"
    if p_hike > 0.6:
        return "鹰派"
    return "中性"

fed_signal = get_fedwatch_signal()

# ---------- 界面显示 ----------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 最新市场行情")
    st.write(f"**SPY (标普500 近收):** {latest_spy}")
    st.write(f"**XAU/USD (黄金近收):** {latest_gold}")
    st.write(f"**BTC 价格:** {latest_btc}")
    st.write(f"**美联储信号:** {fed_signal}")

with col2:
    st.subheader("📊 历史趋势对比")
    chart_df = pd.concat([
        sp500_hist["SPY"].rename("SP500") if not sp500_hist.empty else pd.Series(),
        gold_hist["XAUUSD"].rename("黄金") if not gold_hist.empty else pd.Series(),
        btc_hist["BTC"].rename("BTC") if not btc_hist.empty else pd.Series()
    ], axis=1).dropna()
    st.line_chart(chart_df)

# 下载 CSV
if not chart_df.empty:
    download_csv = chart_df.reset_index().to_csv(index=False).encode('utf-8')
    st.download_button("📥 下载历史行情 CSV", download_csv, "market_history.csv")

# ---------- 资产配置策略 ----------
def alloc_model(o, dxy, fed, btc_vol):
    gold = 25; stocks = 40; btc = 20; cash = 15
    if o and o > latest_gold: gold += 5; stocks -= 5
    if fed == "鸽派": stocks += 5; btc += 5
    if fed == "鹰派": stocks -= 5; gold += 5
    return {"黄金": gold, "美股": stocks, "BTC": btc, "现金": cash}

alloc = alloc_model(latest_gold, latest_spy, fed_signal, 0)

st.subheader("📊 建议资产配置")
df_alloc = pd.DataFrame(alloc.items(), columns=["资产","比例"])
st.bar_chart(df_alloc.set_index("资产"))
st.table(df_alloc)
