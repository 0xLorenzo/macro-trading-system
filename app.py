import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="宏观交易系统 V8", layout="wide")

# ---------- 顶部 Banner ----------
st.markdown("""
<div style="background-color:#1E3A8A;padding:15px;border-radius:8px;text-align:center;color:white">
<h1>🌍 宏观交易策略系统 V8</h1>
<p>实时获取 SP500、黄金、BTC 历史数据，生成动态资产配置策略。</p>
</div>
""", unsafe_allow_html=True)

# ---------- 获取数据 ----------
@st.cache_data(ttl=3600)
def get_sp500_history():
    try:
        import yfinance as yf
        df = yf.download("SPY", period="6mo")
        if df.empty:
            df = yf.download("^GSPC", period="6mo")
        if df.empty:
            return pd.DataFrame()
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        return df[[col]].rename(columns={col:"SP500"})
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_gold_history():
    try:
        import yfinance as yf
        df = yf.download("GC=F", period="6mo")
        if df.empty:
            return pd.DataFrame()
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        df = df[[col]].rename(columns={col:"黄金"})
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_btc_history():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=180"
        data = requests.get(url).json()
        prices = pd.DataFrame(data["prices"], columns=["timestamp","BTC"])
        prices["date"] = pd.to_datetime(prices["timestamp"], unit='ms')
        prices = prices.set_index("date")
        prices["BTC"] = prices["BTC"].astype(float)
        return prices[["BTC"]]
    except:
        return pd.DataFrame()

sp500_hist = get_sp500_history()
gold_hist = get_gold_history()
btc_hist = get_btc_history()

# ---------- 安全获取最新价格 ----------
def safe_latest(df, col_name):
    if df.empty or col_name not in df.columns:
        return None
    val = df[col_name].iloc[-1]
    try:
        val = float(val)
        return None if np.isnan(val) else round(val,2)
    except:
        return None

latest_sp500 = safe_latest(sp500_hist, "SP500")
latest_gold = safe_latest(gold_hist, "黄金")
latest_btc = safe_latest(btc_hist, "BTC")

# ---------- 美联储随机信号 ----------
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

# ---------- 左右布局 ----------
col1, col2 = st.columns([1,2])

with col1:
    st.subheader("📈 最新市场行情")
    st.metric("SP500 (SPY)", latest_sp500)
    st.caption("数据来源：Yahoo Finance SPY ETF 近 6 个月价格")
    st.metric("黄金 (XAU/USD)", latest_gold)
    st.caption("数据来源：Yahoo Finance 黄金期货 GC=F")
    st.metric("BTC", latest_btc)
    st.caption("数据来源：CoinGecko API, BTC/USD")
    st.metric("美联储信号", fed_signal)
    st.caption("随机模拟信号，可升级为 CME FedWatch 实时概率")

with col2:
    st.subheader("📊 历史趋势对比")
    series_list = []

    if not sp500_hist.empty:
        s = sp500_hist["SP500"].copy()
        s.name = "SP500"
        series_list.append(s)

    if not gold_hist.empty:
        s = gold_hist["黄金"].copy()
        s.name = "黄金"
        series_list.append(s)

    if not btc_hist.empty:
        s = btc_hist["BTC"].copy()
        s.name = "BTC"
        series_list.append(s)

    if series_list:
        chart_df = pd.concat(series_list, axis=1).dropna()
        st.line_chart(chart_df)
        download_csv = chart_df.reset_index().to_csv(index=False).encode('utf-8')
        st.download_button("📥 下载历史行情 CSV", download_csv, "market_history.csv")
        st.caption("折线图显示近 6 个月 SP500、黄金、BTC 收盘价对比")
    else:
        st.warning("没有可用历史数据显示折线图")

# ---------- 动态资产配置策略 ----------
def alloc_model(latest_gold_val, latest_sp500_val, fed_signal, btc_vol):
    gold = 25
    stocks = 40
    btc = 20
    cash = 15

    def dynamic_threshold(df):
        if df.empty:
            return None
        mean_val = df.iloc[-60:].mean()
        std_val = df.iloc[-60:].std()
        return mean_val, std_val

    gold_thresh = dynamic_threshold(gold_hist["黄金"]) if not gold_hist.empty else (1800,50)
    sp500_thresh = dynamic_threshold(sp500_hist["SP500"]) if not sp500_hist.empty else (450,20)

    # ---------- 黄金动态调整 ----------
    if latest_gold_val is not None and gold_thresh is not None:
        mean, std = gold_thresh
        if mean is not None and std is not None:
            if latest_gold_val > mean + std:
                gold += 5
                stocks -= 5

    # ---------- SP500动态调整 ----------
    if latest_sp500_val is not None and sp500_thresh is not None:
        mean, std = sp500_thresh
        if mean is not None and std is not None:
            if latest_sp500_val > mean + std:
                stocks += 5
                gold -= 5

    # ---------- 美联储信号调整 ----------
    if fed_signal == "鸽派":
        stocks += 5
        btc += 5
    elif fed_signal == "鹰派":
        stocks -= 5
        gold += 5

    return {"黄金": gold, "美股": stocks, "BTC": btc, "现金": cash}

alloc = alloc_model(latest_gold, latest_sp500, fed_signal, 0)

st.subheader("📊 建议资产配置")
df_alloc = pd.DataFrame(alloc.items(), columns=["资产","比例"])
st.bar_chart(df_alloc.set_index("资产"))
st.table(df_alloc)

with st.expander("策略细节与逻辑说明"):
    st.markdown(f"""
- **黄金**：动态参考值 = 过去 3 个月均值 ± 1 标准差 (最新值 {latest_gold})  
- **SP500**：动态参考值 = 过去 3 个月均值 ± 1 标准差 (最新值 {latest_sp500})  
- **BTC**：根据 Fed 信号 + 波动性微调配置 (最新值 {latest_btc})  
- **美联储信号**：鸽派增加股票/BTC，鹰派增加黄金  
- **现金**：保持 15% 流动性  
- **数据来源**：
    - SP500: Yahoo Finance SPY ETF
    - 黄金: Yahoo Finance 黄金期货 GC=F
    - BTC: CoinGecko API
    - 美联储信号: 随机模拟
""")
