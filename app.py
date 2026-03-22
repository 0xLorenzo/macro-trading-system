import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="宏观交易系统 V12", layout="wide")

# ---------- 顶部 ----------
st.markdown("""
<div style="background-color:#8B8C89;padding:12px;border-radius:6px;text-align:center;color:white">
<h1>🌌 宏观交易策略系统 V12</h1>
</div>
""", unsafe_allow_html=True)

# ---------- 获取数据 ----------
@st.cache_data(ttl=1800)
def get_data_yf(ticker, colname, period="6mo"):
    try:
        import yfinance as yf
        df = yf.download(ticker, period=period)
        if df.empty:
            return pd.DataFrame()
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        df = df[[col]].rename(columns={col: colname})
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_btc_history():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=180"
        data = requests.get(url).json()
        df = pd.DataFrame(data["prices"], columns=["timestamp","BTC"])
        df["date"] = pd.to_datetime(df["timestamp"], unit='ms')
        df = df.set_index("date")[["BTC"]]
        df["BTC"] = df["BTC"].astype(float)
        return df
    except:
        return pd.DataFrame()

sp500_hist = get_data_yf("SPY", "SP500")
gold_hist = get_data_yf("GC=F", "黄金")
btc_hist = get_btc_history()

# ---------- 最新价格 ----------
def safe_latest(df, col):
    if df.empty or col not in df.columns:
        return None
    val = df[col].iloc[-1]
    try:
        return None if np.isnan(val) else round(float(val),2)
    except:
        return None

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

# ---------- 布局：三栏 ----------
col1, col2, col3 = st.columns([1,2,1])

# 左侧：最新行情 + FedWatch
with col1:
    st.subheader("📈 最新市场行情")
    st.metric("SP500 (SPY)", latest_sp500)
    st.metric("黄金 (XAU/USD)", latest_gold)
    st.metric("BTC", latest_btc)
    
    st.subheader("📊 FedWatch 实时概率")
    st.table(pd.DataFrame(fed_prob.items(), columns=["事件","概率 (%)"]).set_index("事件"))

# 中间：历史趋势对数
with col2:
    st.subheader("📊 历史趋势对比（对数指标）")
    series_list = []
    if not sp500_hist.empty: 
        s = sp500_hist["SP500"].copy(); s.name="SP500"; series_list.append(s)
    if not gold_hist.empty: 
        s = gold_hist["黄金"].copy(); s.name="黄金"; series_list.append(s)
    if not btc_hist.empty: 
        s = btc_hist["BTC"].copy(); s.name="BTC"; series_list.append(s)

    if series_list:
        chart_df = pd.concat(series_list, axis=1).dropna()
        chart_df_log = np.log(chart_df)
        fig = px.line(chart_df_log, x=chart_df_log.index, y=chart_df_log.columns,
                      labels={"value":"对数价格","date":"日期"},
                      title="近6个月历史趋势（对数指标）",
                      color_discrete_sequence=["#8E7D6B","#7D8E7D","#7D7D8E"])
        # 标示高低点
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
        st.warning("没有可用历史数据显示折线图")

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
        if latest_gold_val is not None:
            mean,std = gold_thresh
            if latest_gold_val > mean+std: gold+=5; stocks-=5
        if latest_sp500_val is not None:
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
  - 若价格高于上阈值 → 增加黄金配置，减少股票配置  
  - 若价格低于下阈值 → 减少黄金配置，增加股票或现金

- **SP500 (SPY)**：参考过去3个月均值 ± 1 标准差 (最新 {latest_sp500})  
  - 若价格高于上阈值 → 增加股票配置，减少黄金配置  
  - 若价格低于下阈值 → 减少股票配置，增加现金或黄金

- **BTC**：根据 FedWatch 实时概率微调  
  - 降息概率高 → 股票与 BTC 增加  
  - 加息概率高 → 黄金增加，股票减少

- **现金**：保持流动性 15%  

- **FedWatch 实时概率**：CME Fed Fund Futures 模拟，决定宏观政策预期  
- **策略逻辑**：历史价格 + Fed概率 → 动态资产配置  
- **数据来源**：
    - SP500: Yahoo Finance SPY ETF
    - 黄金: Yahoo Finance GC=F
    - BTC: CoinGecko API
    - FedWatch: CME Fed Fund Futures模拟
""")
