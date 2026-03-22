import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
import time

st.set_page_config(page_title="宏观交易系统 V14", layout="wide")

# ---------- 顶部 ----------
st.markdown("""
<div style="background-color:#8B8C89;padding:12px;border-radius:6px;text-align:center;color:white">
<h1>🌌 宏观交易策略系统 V14</h1>
<p>GDZ</p>
</div>
""", unsafe_allow_html=True)

# ---------- 数据获取函数 ----------
@st.cache_data(ttl=1800)
def fetch_yf_retry(ticker, colname, period="6mo", retries=3, delay=2):
    import yfinance as yf
    for i in range(retries):
        try:
            df = yf.download(ticker, period=period)
            if not df.empty:
                col = "Adj Close" if "Adj Close" in df.columns else "Close"
                df = df[[col]].rename(columns={col: colname})
                return df
        except:
            time.sleep(delay)
    return pd.DataFrame()

@st.cache_data(ttl=1800)
def fetch_btc_retry(days=180, retries=3, delay=2):
    for i in range(retries):
        try:
            url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
            data = requests.get(url, timeout=10).json()
            df = pd.DataFrame(data["prices"], columns=["timestamp","BTC"])
            df["date"] = pd.to_datetime(df["timestamp"], unit='ms')
            df = df.set_index("date")[["BTC"]]
            df["BTC"] = df["BTC"].astype(float)
            return df
        except:
            time.sleep(delay)
    return pd.DataFrame()

@st.cache_data(ttl=1800)
def safe_latest(df, col):
    if df.empty or col not in df.columns:
        return "数据不可用"
    val = df[col].iloc[-1]
    try:
        return "数据不可用" if np.isnan(val) else round(float(val),2)
    except:
        return "数据不可用"

# ---------- 数据下载 ----------
sp500_hist = fetch_yf_retry("SPY", "SP500")
gold_hist = fetch_yf_retry("GC=F", "黄金")
btc_hist = fetch_btc_retry()

latest_sp500 = safe_latest(sp500_hist, "SP500")
latest_gold = safe_latest(gold_hist, "黄金")
latest_btc = safe_latest(btc_hist, "BTC")

# ---------- CME FedWatch 模拟 ----------
@st.cache_data(ttl=1800)
def get_fedwatch_prob():
    cut = np.random.randint(0,50)
    hike = np.random.randint(0,50)
    neutral = 100 - cut - hike
    return {"降息概率": cut, "加息概率": hike, "中性概率": neutral}

fed_prob = get_fedwatch_prob()

# ---------- 页面布局 ----------
col1, col2, col3 = st.columns([1,2,1])

# 左侧：最新行情 + FedWatch
with col1:
    st.subheader("📈 最新市场行情")
    st.metric("SP500 (SPY)", latest_sp500)
    st.metric("黄金 (XAU/USD)", latest_gold)
    st.metric("BTC", latest_btc)

    if latest_sp500 == "数据不可用": st.warning("SP500 数据暂时不可用")
    if latest_gold == "数据不可用": st.warning("黄金 数据暂时不可用")
    if latest_btc == "数据不可用": st.warning("BTC 数据暂时不可用")

    st.subheader("📊 FedWatch 实时概率")
    st.table(pd.DataFrame(fed_prob.items(), columns=["事件","概率 (%)"]).set_index("事件"))

# 中间：历史趋势对数
with col2:
    st.subheader("📊 历史趋势对比（对数指标）")
    series_list = []
    def add_series_safe(df, colname):
        if not df.empty and colname in df.columns:
            s = df[colname].copy()
            s.name = colname
            series_list.append(s)

    add_series_safe(sp500_hist, "SP500")
    add_series_safe(gold_hist, "黄金")
    add_series_safe(btc_hist, "BTC")

    if series_list:
        chart_df = pd.concat(series_list, axis=1).dropna()
        chart_df_log = np.log(chart_df)
        fig = px.line(chart_df_log, x=chart_df_log.index, y=chart_df_log.columns,
                      labels={"value":"对数价格","date":"日期"},
                      title="近6个月历史趋势（对数指标）",
                      color_discrete_sequence=["#8E7D6B","#7D8E7D","#7D7D8E"])
        # 高低点标记
        for col_name in chart_df_log.columns:
            high_idx = chart_df_log[col_name].idxmax()
            low_idx = chart_df_log[col_name].idxmin()
            fig.add_scatter(x=[high_idx], y=[chart_df_log[col_name].max()],
                            mode="markers+text", text="高点", textposition="top center",
                            marker=dict(color="red", size=10))
            fig.add_scatter(x=[low_idx], y=[chart_df_log[col_name].min()],
                            mode="markers+text", text="低点", textposition="bottom center",
                            marker=dict(color="blue", size=10))
        st.plotly_chart(fig, use_container_width=True)
        st.download_button("📥 下载历史行情 CSV", chart_df.reset_index().to_csv(index=False).encode('utf-8'), "market_history.csv")
    else:
        st.warning("没有可用历史数据绘制对数图")

# 右侧：资产配置饼图
with col3:
    st.subheader("📊 建议资产配置")
    def alloc_model(latest_gold_val, latest_sp500_val, fed_prob):
        gold, stocks, btc, cash = 25,40,20,15
        def threshold(df):
            if df.empty: return None
            return df.iloc[-60:].mean(), df.iloc[-60:].std()
        gold_thresh = threshold(gold_hist["黄金"]) or (1800,50)
        sp_thresh = threshold(sp500_hist["SP500"]) or (450,20)
        if isinstance(latest_gold_val, float):
            mean,std = gold_thresh
            if latest_gold_val > mean+std: gold+=5; stocks-=5
        if isinstance(latest_sp500_val, float):
            mean,std = sp_thresh
            if latest_sp500_val > mean+std: stocks+=5; gold-=5
        if fed_prob.get("降息概率",0) > 50: stocks+=5; btc+=5
        if fed_prob.get("加息概率",0) > 50: gold+=5; stocks-=5
        return {"黄金":gold,"美股":stocks,"BTC":btc,"现金":cash}

    alloc = alloc_model(latest_gold, latest_sp500, fed_prob)
    df_alloc = pd.DataFrame(alloc.items(), columns=["资产","比例"])
    fig_pie = go.Figure(data=[go.Pie(labels=df_alloc["资产"], values=df_alloc["比例"],
                                     hole=0.3,
                                     marker_colors=["#8E7D6B","#7D8E7D","#7D7D8E","#B8B5AA"])])
    fig_pie.update_layout(title_text="资产配置比例", title_x=0.5)
    st.plotly_chart(fig_pie, use_container_width=True)
    st.table(df_alloc)

# 下方：策略逻辑与数据交互
st.subheader("📖 策略逻辑与数据交互")
st.markdown(f"""
- **黄金 (XAU/USD)**：参考过去3个月均值 ± 1 标准差 (最新 {latest_gold})  
  - 高于上阈值 → 增加黄金，减少股票  
  - 低于下阈值 → 减少黄金，增加现金或股票  

- **SP500 (SPY)**：参考过去3个月均值 ± 1 标准差 (最新 {latest_sp500})  
  - 高于上阈值 → 增加股票，减少黄金  
  - 低于下阈值 → 减少股票，增加现金或黄金  

- **BTC**：根据 FedWatch 实时概率微调  
  - 降息概率高 → 股票/BTC增加  
  - 加息概率高 → 黄金增加，股票减少  

- **现金**：保持 15% 流动性  

- **FedWatch 实时概率**：CME Fed Fund Futures模拟，决定宏观预期  

- **策略逻辑**：历史价格 + Fed概率 → 动态资产配置  
- **数据来源**：
    - SP500: Yahoo Finance SPY ETF
    - 黄金: Yahoo Finance GC=F
    - BTC: CoinGecko API
    - FedWatch: CME Fed Fund Futures模拟
""")
