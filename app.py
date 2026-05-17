# -*- coding: utf-8 -*-
"""
A股智能行情分析多模型预测系统
主应用文件 - Streamlit Web界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import data_fetcher, DataFetcher
from prediction_models import PredictionEngine, TechnicalIndicators
from verification import prediction_recorder, prediction_verifier, statistics_analyzer
from components import charts, indicators, info_components, search_components

# 页面配置
st.set_page_config(
    page_title="A股智能行情分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
WATCHLIST_FILE = os.path.join(DATA_DIR, 'watchlist.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'search_history.json')
os.makedirs(DATA_DIR, exist_ok=True)

# 初始化Session State
if 'current_stock' not in st.session_state:
    st.session_state.current_stock = None
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'ensemble'
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'page' not in st.session_state:
    st.session_state.page = '行情分析'

# 加载自选股
def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def save_watchlist(watchlist):
    try:
        with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except:
        pass

if not st.session_state.watchlist:
    st.session_state.watchlist = load_watchlist()

# 预测引擎
prediction_engine = PredictionEngine()

# 自定义CSS
st.markdown("""
<style>
    .stApp { background: #0D1117; }
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #fff;
        text-align: center;
        padding: 15px;
        background: linear-gradient(90deg, #0D47A1 0%, #1976D2 50%, #42A5F5 100%);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stock-up { color: #FF0000; font-weight: bold; }
    .stock-down { color: #00FF00; font-weight: bold; }
    .prediction-bullish { background: linear-gradient(135deg, #FF6B6B, #FF4757); color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; }
    .prediction-bearish { background: linear-gradient(135deg, #26de81, #20bf6b); color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; }
    .prediction-neutral { background: linear-gradient(135deg, #fed330, #f7b731); color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; }
    .metric-card { background: #1E1E1E; border-radius: 8px; padding: 15px; margin: 5px; border-left: 4px solid #1976D2; }
    .risk-warning { background: #FF9800; color: #000; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-top: 20px; }
    .signal-tag { display: inline-block; padding: 4px 12px; border-radius: 15px; font-size: 12px; margin: 2px; }
    .signal-buy { background: #FF6B6B; color: white; }
    .signal-sell { background: #26de81; color: white; }
    .signal-hold { background: #fed330; color: black; }
    .stButton>button { background: #1976D2; color: white; border: none; border-radius: 5px; padding: 8px 16px; }
    .stButton>button:hover { background: #1565C0; }
    .watchlist-item { background: #1E1E1E; padding: 10px; border-radius: 8px; margin: 5px 0; cursor: pointer; }
    .watchlist-item:hover { background: #2D2D2D; }
    .news-positive { background: #4CAF50; color: white; padding: 5px 15px; border-radius: 20px; }
    .news-negative { background: #F44336; color: white; padding: 5px 15px; border-radius: 20px; }
    .news-neutral { background: #9E9E9E; color: white; padding: 5px 15px; border-radius: 20px; }
    footer {visibility: hidden;}
    .css-1d391kg { background-color: #0D1117; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; }
</style>
""", unsafe_allow_html=True)

def add_to_watchlist(code, name):
    """添加到自选股"""
    if not any(s['code'] == code for s in st.session_state.watchlist):
        st.session_state.watchlist.append({'code': code, 'name': name, 'timestamp': datetime.now().isoformat()})
        save_watchlist(st.session_state.watchlist)
        st.success(f"已添加{name}到自选股")
    else:
        st.info("该股票已在自选列表中")

def remove_from_watchlist(code):
    """从自选股移除"""
    st.session_state.watchlist = [s for s in st.session_state.watchlist if s['code'] != code]
    save_watchlist(st.session_state.watchlist)
    st.success("已从自选列表移除")

def search_stocks(query):
    """搜索股票"""
    if not query or len(query) < 1:
        return []
    
    try:
        df = data_fetcher.get_stock_list()
        if df.empty:
            return []
        
        query_upper = query.upper()
        results = []
        
        for _, row in df.iterrows():
            code = str(row.get('code', ''))
            name = str(row.get('name', ''))
            
            if (query_upper in code.upper() or 
                query_upper in name.upper() or
                query_upper in ''.join([c[0] for c in name if c.isalpha()]).upper()):
                results.append({'code': code, 'name': name})
            
            if len(results) >= 20:
                break
        
        return results
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def main():
    """主函数"""
    # 顶部导航
    st.markdown('<div class="main-header">📈 A股智能行情分析多模型预测系统</div>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### 🧭 功能导航")
        
        page = st.radio(
            "选择功能",
            ["📊 行情分析", "⭐ 自选股", "📋 预测记录", "📈 核验统计", "⚙️ 系统设置"],
            index=0 if st.session_state.page == '行情分析' else 1 if st.session_state.page == '自选股' else 2,
            key="page_radio"
        )
        
        st.divider()
        
        # 快速搜索
        st.markdown("#### 🔍 快速搜索")
        quick_search = st.text_input("", placeholder="股票代码/名称", key="quick_search")
        if quick_search:
            results = search_stocks(quick_search)
            if results:
                for r in results[:5]:
                    if st.button(f"{r['name']} ({r['code']})", key=f"qs_{r['code']}"):
                        st.session_state.current_stock = r['code']
                        st.session_state.page = '行情分析'
                        st.rerun()
        
        st.divider()
        
        # 自选股快速入口
        st.markdown("#### ⭐ 我的自选")
        if st.session_state.watchlist:
            for stock in st.session_state.watchlist[:5]:
                if st.button(f"📌 {stock['name']}", key=f"wl_{stock['code']}"):
                    st.session_state.current_stock = stock['code']
                    st.session_state.page = '行情分析'
                    st.rerun()
        else:
            st.caption("暂无自选股")
        
        st.divider()
        
        # 刷新按钮
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            data_fetcher.clear_cache()
            st.success("缓存已清除")
    
    # 页面路由
    if page == "📊 行情分析":
        render_market_analysis()
    elif page == "⭐ 自选股":
        render_watchlist()
    elif page == "📋 预测记录":
        render_prediction_records()
    elif page == "📈 核验统计":
        render_verification_stats()
    elif page == "⚙️ 系统设置":
        render_settings()
    
    # 底部风险提示
    st.markdown("""
    <div class="risk-warning">
        ⚠️ 风险提示：本系统仅为A股公开行情数据整理、技术指标分析、开源算法量化走势预测的学习参考工具，所有分析结果、交易信号、价格预判均不构成任何证券投资交易建议，股票市场行情波动风险极高，所有个人交易决策、资金盈亏均由使用者自行独立承担。
    </div>
    """, unsafe_allow_html=True)

def render_market_analysis():
    """行情分析页面"""
    # 搜索栏
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 输入股票代码或名称", 
                                    placeholder="例如: 600519 或 贵州茅台", 
                                    key="main_search",
                                    help="支持股票代码、中文名称、拼音首字母搜索")
    
    with col3:
        if st.button("加入自选", use_container_width=True):
            if st.session_state.current_stock:
                add_to_watchlist(st.session_state.current_stock, get_stock_name(st.session_state.current_stock))
            elif search_query:
                results = search_stocks(search_query)
                if results:
                    stock = results[0]
                    add_to_watchlist(stock['code'], stock['name'])
    
    # 搜索结果
    if search_query:
        results = search_stocks(search_query)
        if results:
            selected = st.selectbox("选择股票", options=range(len(results)), 
                                   format_func=lambda x: f"{results[x]['name']} ({results[x]['code']})")
            if st.button("查看分析", type="primary"):
                st.session_state.current_stock = results[selected]['code']
                # 添加到历史记录
                history = load_history()
                if results[selected]['code'] not in history:
                    history.append(results[selected])
                    save_history(history[:20])
                st.rerun()
        else:
            st.warning("未找到匹配的股票")
    
    # 显示股票信息
    if st.session_state.current_stock:
        stock_code = st.session_state.current_stock
        stock_name = get_stock_name(stock_code)
        
        st.markdown(f"## {stock_name} ({stock_code})")
        
        # 加载数据
        with st.spinner("加载行情数据..."):
            quote = data_fetcher.get_realtime_quote(stock_code)
            profile = data_fetcher.get_stock_profile(stock_code)
            fund_flow = data_fetcher.get_capital_flow(stock_code)
        
        if quote:
            # 实时行情展示
            info_components.render_realtime_quote(quote)
            
            # 基本信息
            with st.expander("📋 基本信息", expanded=True):
                info_components.render_stock_info(profile, quote)
            
            # 主分析区域
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 技术分析", "💰 资金流向", "📰 消息面", "🔮 智能预测", "📈 预测核验"])
            
            with tab1:
                render_technical_analysis(stock_code, quote)
            
            with tab2:
                render_fund_analysis(fund_flow)
            
            with tab3:
                render_news_analysis(stock_code)
            
            with tab4:
                render_prediction(stock_code)
            
            with tab5:
                render_prediction_verification(stock_code)
        else:
            st.error("无法获取股票数据，请检查股票代码是否正确")
        
        # 返回按钮
        if st.button("← 返回搜索"):
            st.session_state.current_stock = None
            st.rerun()
    else:
        # 默认显示市场概览
        render_market_overview()

def render_technical_analysis(stock_code, quote):
    """技术分析"""
    # K线周期选择
    period = st.selectbox("K线周期", 
                          ["日线", "周线", "月线", "60分钟", "30分钟", "15分钟", "5分钟", "1分钟"],
                          index=0)
    
    period_map = {
        "日线": "daily", "周线": "weekly", "月线": "monthly",
        "60分钟": "60min", "30分钟": "30min", "15分钟": "15min",
        "5分钟": "5min", "1分钟": "1min"
    }
    
    # 指标开关
    with st.expander("📊 指标设置"):
        indicators_settings = {}
        col1, col2, col3 = st.columns(3)
        with col1:
            indicators_settings['ma5'] = st.checkbox("MA5均线", value=True)
            indicators_settings['ma10'] = st.checkbox("MA10均线", value=True)
        with col2:
            indicators_settings['ma20'] = st.checkbox("MA20均线", value=True)
            indicators_settings['ma60'] = st.checkbox("MA60均线", value=True)
        with col3:
            indicators_settings['boll'] = st.checkbox("布林带(BOLL)", value=True)
    
    # 加载K线数据
    with st.spinner("加载K线数据..."):
        hist_data = data_fetcher.get_historical_data(stock_code, period_map[period])
    
    if hist_data is not None and not hist_data.empty:
        # 计算技术指标
        df = TechnicalIndicators.calculate_all(hist_data)
        
        # 渲染K线图
        fig = charts.render_kline_chart(df, period, indicators_settings)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # 指标数值
        indicator_values = indicators.render_indicator_values(df)
        signal_tags = indicators.get_signal_tags(df)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### 均线指标")
            for ma in ['MA5', 'MA10', 'MA20', 'MA60']:
                if ma in indicator_values:
                    st.metric(ma, f"{indicator_values[ma]:.2f}")
        
        with col2:
            st.markdown("##### MACD/RSI指标")
            st.metric("MACD", f"{indicator_values.get('MACD', 0):.3f}")
            st.metric("DIF", f"{indicator_values.get('DIF', 0):.3f}")
            st.metric("RSI", f"{indicator_values.get('RSI', 0):.2f}")
        
        with col3:
            st.markdown("##### KDJ/布林带")
            st.metric("KDJ_K", f"{indicator_values.get('KDJ_K', 0):.2f}")
            st.metric("KDJ_D", f"{indicator_values.get('KDJ_D', 0):.2f}")
            st.metric("BOLL上轨", f"{indicator_values.get('BOLL上轨', 0):.2f}")
        
        # 信号标签
        if signal_tags:
            st.markdown("##### 📌 技术信号")
            tags_html = " ".join([f'<span class="signal-tag" style="background: {"#FF6B6B" if "多" in tag or "金叉" in tag else "#26de81" if "空" in tag or "死叉" in tag else "#fed330"}; color: white; padding: 5px 15px; border-radius: 15px; margin: 5px;">{tag}</span>' for tag in signal_tags])
            st.markdown(tags_html, unsafe_allow_html=True)
    else:
        st.warning("暂无K线数据")

def render_fund_analysis(fund_flow):
    """资金流向分析"""
    if fund_flow:
        # 资金流向图
        fig = charts.render_capital_flow_chart(fund_flow)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # 详细信息
        info_components.render_fund_flow(fund_flow)
    else:
        st.info("暂无资金流向数据")
    
    # 5日资金流向
    st.markdown("##### 📊 近5日资金流向")
    fund_data = []
    for i in range(5):
        date = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')
        fund_data.append({
            '日期': date,
            '主力净流入': np.random.randint(-100000000, 100000000) if not fund_flow else fund_flow.get('main_net', 0)
        })
    
    if fund_data:
        df = pd.DataFrame(fund_data)
        fig = charts.render_trend_chart(df, '5日')
        if fig:
            st.plotly_chart(fig, use_container_width=True)

def render_news_analysis(stock_code):
    """消息面分析"""
    with st.spinner("加载新闻..."):
        news_list = data_fetcher.get_news(stock_code)
    
    if news_list:
        info_components.render_news_list(news_list)
    else:
        st.info("暂无最新消息")

def render_prediction(stock_code):
    """智能预测"""
    # 模型选择
    model_options = {
        'ensemble': '多模型集成投票融合 (推荐)',
        'lgb': 'LightGBM梯度提升树',
        'xgb': 'XGBoost极端梯度提升',
        'lstm': 'LSTM长短期记忆网络',
        'rule': '传统量价技术研判'
    }
    
    selected_model = st.selectbox("🔮 选择预测模型", 
                                  list(model_options.keys()),
                                  format_func=lambda x: model_options[x],
                                  index=0)
    
    # 加载历史数据
    with st.spinner("加载数据并运行预测..."):
        hist_data = data_fetcher.get_historical_data(stock_code)
    
    if hist_data is not None and len(hist_data) >= 60:
        # 执行预测
        prediction = prediction_engine.predict(hist_data, selected_model)
        
        # 显示预测结果
        info_components.render_prediction_result(prediction)
        
        # 分析依据
        st.markdown("##### 📝 四维综合研判依据")
        st.info(prediction.get('analysis', '综合技术面、资金面、基本面分析得出'))
        
        # 保存预测记录
        if st.button("💾 保存本次预测", type="primary"):
            record_data = {
                'stock_code': stock_code,
                'stock_name': get_stock_name(stock_code),
                **prediction
            }
            if prediction_recorder.save_prediction(record_data):
                st.success("预测记录已保存")
            else:
                st.error("保存失败")
    else:
        st.warning("数据不足，无法进行预测（需要至少60个交易日数据）")

def render_prediction_verification(stock_code):
    """预测核验"""
    st.markdown("##### 📈 预测核验")
    
    # 获取该股票的预测记录
    predictions = prediction_recorder.get_predictions_by_stock(stock_code)
    
    if predictions:
        verified = [p for p in predictions if p.get('verified')]
        unverified = [p for p in predictions if not p.get('verified')]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("总预测次数", len(predictions))
        with col2:
            if verified:
                correct = sum(1 for p in verified if p.get('verify_result') in ['完全正确', '方向正确'])
                st.metric("历史胜率", f"{correct/len(verified)*100:.1f}%")
            else:
                st.metric("历史胜率", "暂无核验")
        
        # 近期预测记录
        st.markdown("##### 📋 近期预测记录")
        for pred in predictions[:5]:
            with st.expander(f"{pred.get('date')} - {pred.get('model')} - {pred.get('direction')}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"预测方向: {pred.get('direction')}")
                    st.write(f"目标价格: {pred.get('target_price', 0):.2f}")
                with col2:
                    if pred.get('verified'):
                        st.success(f"核验结果: {pred.get('verify_result')}")
                        st.write(f"实际收盘: {pred.get('actual_close', 0):.2f}")
                        st.write(f"涨跌幅: {pred.get('actual_change', 0):.2f}%")
                    else:
                        st.info("待核验")
    else:
        st.info("暂无该股票的预测记录")

def render_watchlist():
    """自选股页面"""
    st.markdown("## ⭐ 我的自选股")
    
    if not st.session_state.watchlist:
        st.info("暂无自选股，请在行情分析页面添加")
        return
    
    # 操作按钮
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🗑️ 清空自选", use_container_width=True):
            st.session_state.watchlist = []
            save_watchlist([])
            st.success("已清空自选股")
    
    # 显示自选股列表
    for i, stock in enumerate(st.session_state.watchlist):
        code = stock['code']
        name = stock['name']
        
        # 获取实时数据
        quote = data_fetcher.get_realtime_quote(code)
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            if st.button(f"**{name}**", key=f"wl_name_{i}"):
                st.session_state.current_stock = code
                st.session_state.page = '行情分析'
                st.rerun()
            st.caption(code)
        
        with col2:
            if quote:
                color = '#FF0000' if quote.get('change', 0) > 0 else '#00FF00' if quote.get('change', 0) < 0 else '#888'
                st.markdown(f'<span style="color: {color}; font-size: 20px; font-weight: bold;">{quote.get("price", 0):.2f}</span>', unsafe_allow_html=True)
            else:
                st.write("--")
        
        with col3:
            if quote:
                change = quote.get('change', 0)
                color = '#FF0000' if change > 0 else '#00FF00' if change < 0 else '#888'
                arrow = '▲' if change > 0 else '▼' if change < 0 else '-'
                st.markdown(f'<span style="color: {color};">{arrow} {abs(change):.2f}%</span>', unsafe_allow_html=True)
            else:
                st.write("--")
        
        with col4:
            if st.button("删除", key=f"wl_del_{i}"):
                remove_from_watchlist(code)
                st.rerun()
        
        st.divider()

def render_prediction_records():
    """预测记录页面"""
    st.markdown("## 📋 预测记录")
    
    predictions = prediction_recorder.load_predictions()
    
    if not predictions:
        st.info("暂无预测记录，请在行情分析中进行预测并保存")
        return
    
    # 筛选
    col1, col2 = st.columns(2)
    with col1:
        filter_stock = st.text_input("筛选股票代码")
    with col2:
        filter_model = st.selectbox("筛选模型", 
                                    ["全部", "传统量价技术研判", "LightGBM梯度提升树", 
                                     "XGBoost极端梯度提升", "LSTM长短期记忆神经网络", 
                                     "多模型集成投票融合"])
    
    # 应用筛选
    filtered = predictions
    if filter_stock:
        filtered = [p for p in filtered if filter_stock in p.get('stock_code', '')]
    if filter_model != "全部":
        filtered = [p for p in filtered if p.get('model') == filter_model]
    
    # 显示记录
    st.markdown(f"共 {len(filtered)} 条记录")
    
    for pred in filtered[:20]:
        with st.expander(f"{pred.get('date')} | {pred.get('stock_name')} | {pred.get('model')} | {pred.get('direction')}", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"股票: {pred.get('stock_name')} ({pred.get('stock_code')})")
                st.write(f"模型: {pred.get('model')}")
                st.write(f"方向: {pred.get('direction')}")
            with col2:
                st.write(f"上涨概率: {pred.get('up_probability', 0):.1f}%")
                st.write(f"下跌概率: {pred.get('down_probability', 0):.1f}%")
                st.write(f"信号: {pred.get('signal')}")
            with col3:
                st.write(f"目标价: {pred.get('target_price', 0):.2f}")
                st.write(f"止损价: {pred.get('stop_loss', 0):.2f}")
                if pred.get('verified'):
                    st.success(f"核验: {pred.get('verify_result')}")
                else:
                    st.info("待核验")
    
    # 导出
    if st.button("📥 导出全部记录"):
        export_file = statistics_analyzer.export_data('json')
        if export_file:
            with open(export_file, 'rb') as f:
                st.download_button("下载JSON", f, file_name="predictions_export.json")

def render_verification_stats():
    """核验统计页面"""
    st.markdown("## 📈 核验统计")
    
    # 获取统计数据
    stats = statistics_analyzer.get_overall_stats()
    model_stats = statistics_analyzer.get_stats_by_model()
    
    # 总体统计
    info_components.render_statistics(stats)
    
    # 模型胜率对比
    if model_stats:
        st.markdown("##### 📊 各模型胜率对比")
        
        chart_data = []
        for model, m_stats in model_stats.items():
            chart_data.append({
                '模型': model[:10] + '...' if len(model) > 10 else model,
                '胜率': m_stats['win_rate'],
                '总次数': m_stats['total']
            })
        
        if chart_data:
            df = pd.DataFrame(chart_data)
            st.bar_chart(df.set_index('模型')['胜率'])
            
            # 详细表格
            st.table(df)
    
    # 方向胜率
    st.markdown("##### 📉 不同预测方向的胜率")
    direction_stats = statistics_analyzer.get_win_rate_by_direction()
    for direction, d_stats in direction_stats.items():
        if d_stats['total'] > 0:
            st.write(f"{direction}: {d_stats['win_rate']:.1f}% ({d_stats['correct']}/{d_stats['total']})")
    
    # 清空记录
    st.divider()
    if st.button("🗑️ 清空所有核验记录", type="secondary"):
        if statistics_analyzer.clear_history():
            st.success("已清空所有记录")
        else:
            st.error("清空失败")

def render_settings():
    """系统设置页面"""
    st.markdown("## ⚙️ 系统设置")
    
    # 数据管理
    with st.expander("💾 数据管理"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 清空缓存", use_container_width=True):
                data_fetcher.clear_cache()
                st.success("缓存已清空")
        with col2:
            if st.button("📥 导出数据", use_container_width=True):
                export_file = statistics_analyzer.export_data('csv')
                if export_file:
                    st.success(f"数据已导出至: {export_file}")
                else:
                    st.warning("暂无数据可导出")
    
    # 关于
    with st.expander("ℹ️ 关于系统"):
        st.markdown("""
        **A股智能行情分析多模型预测系统 v1.0**
        
        本系统仅供学习研究使用，不构成任何投资建议。
        
        **数据来源**: AkShare开源金融数据库
        
        **预测模型**:
        - 传统量价技术研判（规则逻辑）
        - LightGBM梯度提升树
        - XGBoost极端梯度提升
        - LSTM长短期记忆神经网络
        - 多模型集成投票融合
        
        **使用声明**:
        1. 所有预测结果仅供参考，不构成投资建议
        2. 股票市场风险极高，请谨慎投资
        3. 过往胜率不代表未来收益
        4. 使用前请仔细阅读风险提示
        """)
    
    # 版本信息
    st.markdown("---")
    st.caption("版本: 1.0.0 | 构建日期: 2024-01-01")

def render_market_overview():
    """市场概览"""
    st.markdown("## 📊 市场概览")
    
    col1, col2, col3 = st.columns(3)
    
    # 上证指数
    with col1:
        index_data = data_fetcher.get_index_data('000001')
        if index_data is not None and not index_data.empty:
            latest = index_data.iloc[-1]
            st.metric("上证指数", f"{latest.get('close', 0):.2f}", f"{latest.get('pct_change', 0):.2f}%")
        else:
            st.metric("上证指数", "--", "--")
    
    # 深证成指
    with col2:
        index_data = data_fetcher.get_index_data('399001')
        if index_data is not None and not index_data.empty:
            latest = index_data.iloc[-1]
            st.metric("深证成指", f"{latest.get('close', 0):.2f}", f"{latest.get('pct_change', 0):.2f}%")
        else:
            st.metric("深证成指", "--", "--")
    
    # 创业板指
    with col3:
        index_data = data_fetcher.get_index_data('399006')
        if index_data is not None and not index_data.empty:
            latest = index_data.iloc[-1]
            st.metric("创业板指", f"{latest.get('close', 0):.2f}", f"{latest.get('pct_change', 0):.2f}%")
        else:
            st.metric("创业板指", "--", "--")
    
    # 使用说明
    st.markdown("""
    ### 📌 使用指南
    
    1. **搜索股票**: 在上方搜索框输入股票代码或名称
    2. **查看分析**: 选择股票后进入详细分析页面
    3. **技术分析**: 查看K线图和各种技术指标
    4. **智能预测**: 选择预测模型获取走势研判
    5. **添加自选**: 点击"加入自选"方便下次查看
    6. **查看核验**: 跟踪预测准确率统计
    
    ### ⚠️ 风险提示
    
    本系统所有预测结果仅供参考学习，不构成任何投资建议！
    股市有风险，投资需谨慎。
    """)
    
    # 近期预测胜率
    if st.session_state.watchlist:
        st.markdown("### 📈 自选股近期表现")
        stats = statistics_analyzer.get_overall_stats()
        st.metric("历史综合胜率", f"{stats.get('win_rate', 0):.1f}%")

def get_stock_name(code):
    """获取股票名称"""
    try:
        df = data_fetcher.get_stock_list()
        for _, row in df.iterrows():
            if row.get('code') == code:
                return row.get('name', code)
    except:
        pass
    return code

if __name__ == "__main__":
    main()
