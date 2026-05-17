# -*- coding: utf-8 -*-
"""
UI组件模块
提供K线图、指标面板、资金流等可视化组件
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import plotly.express as px
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class ChartComponents:
    """K线图组件"""
    
    @staticmethod
    def render_kline_chart(data: pd.DataFrame, period: str = '日线', indicators: Dict = None) -> go.Figure:
        """渲染K线图"""
        if data is None or data.empty or len(data) < 2:
            return None
        
        df = data.tail(120).copy()
        
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=('K线图', '成交量', 'MACD')
        )
        
        colors = {'up': '#FF0000', 'down': '#00FF00', 'flat': '#888888'}
        df['color'] = df.apply(lambda x: 'up' if x['close'] >= x['open'] else 'down', axis=1)
        
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='K线',
                increasing_line_color='#FF0000',
                decreasing_line_color='#00FF00',
                increasing_fillcolor='#FF0000',
                decreasing_fillcolor='#00FF00'
            ),
            row=1, col=1
        )
        
        if indicators:
            if indicators.get('ma5', True) and 'ma5' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ma5'], name='MA5', line=dict(color='#FF6B6B', width=1)), row=1, col=1)
            if indicators.get('ma10', True) and 'ma10' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], name='MA10', line=dict(color='#4ECDC4', width=1)), row=1, col=1)
            if indicators.get('ma20', True) and 'ma20' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], name='MA20', line=dict(color='#45B7D1', width=1.5)), row=1, col=1)
            if indicators.get('ma60', True) and 'ma60' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ma60'], name='MA60', line=dict(color='#FFA07A', width=1.5)), row=1, col=1)
            
            if indicators.get('boll', True) and 'boll_upper' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['boll_upper'], name='BOLL上轨', 
                                        line=dict(color='#9400D3', width=1, dash='dash'), opacity=0.7), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['date'], y=df['boll_mid'], name='BOLL中轨', 
                                        line=dict(color='#9400D3', width=1), opacity=0.7), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['date'], y=df['boll_lower'], name='BOLL下轨', 
                                        line=dict(color='#9400D3', width=1, dash='dash'), opacity=0.7), row=1, col=1)
        
        colors_vol = ['#FF0000' if c == 'up' else '#00FF00' for c in df['color']]
        fig.add_trace(
            go.Bar(x=df['date'], y=df['volume'], name='成交量', marker_color=colors_vol, opacity=0.7),
            row=2, col=1
        )
        
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            colors_macd = ['#FF0000' if v >= 0 else '#00FF00' for v in df['macd_hist']]
            fig.add_trace(
                go.Bar(x=df['date'], y=df['macd_hist'], name='MACD柱', marker_color=colors_macd, opacity=0.7),
                row=3, col=1
            )
            fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', line=dict(color='#FF00FF', width=1.5)), row=3, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', line=dict(color='#00FFFF', width=1.5)), row=3, col=1)
        
        fig.update_layout(
            template='plotly_dark',
            height=600,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_rangeslider_visible=False,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def render_minute_chart(data: pd.DataFrame) -> go.Figure:
        """渲染分时图"""
        if data is None or data.empty:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['time'] if 'time' in data.columns else data.index,
            y=data['close'],
            mode='lines',
            name='价格',
            line=dict(color='#FF0000', width=2)
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=400,
            showlegend=True,
            hovermode='x unified',
            xaxis_rangeslider_visible=False
        )
        
        return fig
    
    @staticmethod
    def render_capital_flow_chart(data: Dict) -> go.Figure:
        """渲染资金流向图"""
        if not data:
            return None
        
        labels = ['超大单', '大单', '中单', '小单']
        values = [
            data.get('super_net', 0),
            data.get('big_net', 0),
            data.get('mid_net', 0),
            data.get('small_net', 0)
        ]
        
        colors = ['#FF0000' if v > 0 else '#00FF00' for v in values]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f'{v/10000:.2f}万' for v in values],
            textposition='outside'
        ))
        
        fig.update_layout(
            title='资金流向分布',
            template='plotly_dark',
            height=300,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def render_trend_chart(data: pd.DataFrame, period: str = '5日') -> go.Figure:
        """渲染趋势图"""
        if data is None or data.empty:
            return None
        
        df = data.tail(5) if period == '5日' else data.tail(10) if period == '10日' else data.tail(20)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df.index if hasattr(df.index, '__iter__') else range(len(df)),
            y=df.get('main_net', df['close'] if 'close' in df.columns else []),
            mode='lines+markers',
            name='主力净流入',
            fill='tozeroy',
            line=dict(color='#FF6B6B', width=2)
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=250,
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def render_win_rate_gauge(win_rate: float, title: str = '胜率') -> go.Figure:
        """渲染胜率仪表盘"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=win_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1976D2"},
                'steps': [
                    {'range': [0, 40], 'color': "#FF6B6B"},
                    {'range': [40, 60], 'color': "#FFD700"},
                    {'range': [60, 100], 'color': "#26de81"}
                ],
                'threshold': {
                    'line': {'color': "#FF0000", 'width': 4},
                    'thickness': 0.8,
                    'value': win_rate
                }
            }
        ))
        
        fig.update_layout(height=200, template='plotly_dark')
        return fig
    
    @staticmethod
    def render_probability_chart(up_prob: float, down_prob: float) -> go.Figure:
        """渲染概率图"""
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=['上涨概率', '下跌概率'],
            values=[up_prob, down_prob],
            marker=dict(colors=['#FF0000', '#00FF00']),
            textinfo='label+percent',
            textfont=dict(size=14),
            hole=0.6
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=250,
            showlegend=True
        )
        
        return fig


class IndicatorComponents:
    """技术指标组件"""
    
    @staticmethod
    def render_indicator_values(data: pd.DataFrame) -> Dict[str, float]:
        """渲染指标数值"""
        if data is None or data.empty:
            return {}
        
        latest = data.iloc[-1]
        
        indicators = {
            'MA5': round(latest.get('ma5', 0), 2) if pd.notna(latest.get('ma5')) else 0,
            'MA10': round(latest.get('ma10', 0), 2) if pd.notna(latest.get('ma10')) else 0,
            'MA20': round(latest.get('ma20', 0), 2) if pd.notna(latest.get('ma20')) else 0,
            'MA60': round(latest.get('ma60', 0), 2) if pd.notna(latest.get('ma60')) else 0,
            'MACD': round(latest.get('macd', 0), 3) if pd.notna(latest.get('macd')) else 0,
            'DIF': round(latest.get('macd', 0), 3) if pd.notna(latest.get('macd')) else 0,
            'DEA': round(latest.get('macd_signal', 0), 3) if pd.notna(latest.get('macd_signal')) else 0,
            'KDJ_K': round(latest.get('kdj_k', 0), 2) if pd.notna(latest.get('kdj_k')) else 0,
            'KDJ_D': round(latest.get('kdj_d', 0), 2) if pd.notna(latest.get('kdj_d')) else 0,
            'KDJ_J': round(latest.get('kdj_j', 0), 2) if pd.notna(latest.get('kdj_j')) else 0,
            'BOLL上轨': round(latest.get('boll_upper', 0), 2) if pd.notna(latest.get('boll_upper')) else 0,
            'BOLL中轨': round(latest.get('boll_mid', 0), 2) if pd.notna(latest.get('boll_mid')) else 0,
            'BOLL下轨': round(latest.get('boll_lower', 0), 2) if pd.notna(latest.get('boll_lower')) else 0,
            'RSI': round(latest.get('rsi', 0), 2) if pd.notna(latest.get('rsi')) else 0,
            '量比': round(latest.get('vol_ratio', 0), 2) if pd.notna(latest.get('vol_ratio')) else 0
        }
        
        return indicators
    
    @staticmethod
    def get_signal_tags(data: pd.DataFrame) -> List[str]:
        """获取信号标签"""
        if data is None or data.empty or len(data) < 20:
            return []
        
        tags = []
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        if pd.notna(latest.get('ma5')) and pd.notna(latest.get('ma10')):
            if latest['ma5'] > latest['ma10'] and prev['ma5'] <= prev['ma10']:
                tags.append('MA金叉')
            elif latest['ma5'] < latest['ma10'] and prev['ma5'] >= prev['ma10']:
                tags.append('MA死叉')
        
        if pd.notna(latest.get('kdj_k')) and pd.notna(latest.get('kdj_d')):
            if latest['kdj_k'] > latest['kdj_d'] and prev['kdj_k'] <= prev['kdj_d']:
                tags.append('KDJ金叉')
            elif latest['kdj_k'] < latest['kdj_d'] and prev['kdj_k'] >= prev['kdj_d']:
                tags.append('KDJ死叉')
        
        if pd.notna(latest.get('macd')) and pd.notna(latest.get('macd_signal')):
            if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                tags.append('MACD金叉')
            elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                tags.append('MACD死叉')
        
        if pd.notna(latest.get('rsi')):
            if latest['rsi'] > 70:
                tags.append('RSI超买')
            elif latest['rsi'] < 30:
                tags.append('RSI超卖')
        
        if pd.notna(latest.get('ma5')) and pd.notna(latest.get('ma20')):
            if latest['ma5'] > latest['ma20'] and latest['ma10'] > latest['ma20']:
                tags.append('均线多头')
            elif latest['ma5'] < latest['ma20'] and latest['ma10'] < latest['ma20']:
                tags.append('均线空头')
        
        return tags


class InfoComponents:
    """信息展示组件"""
    
    @staticmethod
    def render_stock_info(info: Dict, quote: Dict) -> None:
        """渲染股票基本信息"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("股票名称", info.get('name', quote.get('name', 'N/A')))
            st.metric("所属行业", info.get('industry', 'N/A'))
        with col2:
            st.metric("总市值", f"{quote.get('market_cap', 0)/100000000:.2f}亿" if quote.get('market_cap') else 'N/A')
            st.metric("流通市值", f"{quote.get('float_cap', 0)/100000000:.2f}亿" if quote.get('float_cap') else 'N/A')
        with col3:
            pe = quote.get('pe', None)
            st.metric("市盈率(PE)", f"{pe:.2f}" if pe else 'N/A')
            pb = quote.get('pb', None)
            st.metric("市净率(PB)", f"{pb:.2f}" if pb else 'N/A')
        with col4:
            st.metric("换手率", f"{quote.get('turnover', 0):.2f}%" if quote.get('turnover') else 'N/A')
            st.metric("量比", f"{quote.get('volume_ratio', 0):.2f}" if quote.get('volume_ratio') else 'N/A')
    
    @staticmethod
    def render_realtime_quote(quote: Dict) -> None:
        """渲染实时行情"""
        price = quote.get('price', 0)
        change = quote.get('change', 0)
        prev_close = quote.get('close_prev', price)
        
        color = '#FF0000' if change > 0 else '#00FF00' if change < 0 else '#888888'
        arrow = '▲' if change > 0 else '▼' if change < 0 else '-'
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 15px; margin: 10px 0;">
            <h2 style="color: {color}; margin: 0; font-size: 48px; font-weight: bold;">
                {price:.2f}
                <span style="font-size: 24px;">{arrow} {abs(change):.2f}%</span>
            </h2>
            <p style="color: #888; margin: 5px 0;">
                今开: {quote.get('open', 0):.2f} | 
                最高: <span style="color: #FF0000;">{quote.get('high', 0):.2f}</span> | 
                最低: <span style="color: #00FF00;">{quote.get('low', 0):.2f}</span> | 
                昨收: {prev_close:.2f}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_prediction_result(prediction: Dict) -> None:
        """渲染预测结果"""
        direction = prediction.get('direction', '区间震荡')
        
        if direction == '看涨':
            direction_class = 'prediction-bullish'
        elif direction == '看跌':
            direction_class = 'prediction-bearish'
        else:
            direction_class = 'prediction-neutral'
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 15px; padding: 20px; margin: 10px 0;">
            <div style="text-align: center; margin-bottom: 15px;">
                <span class="{direction_class}" style="font-size: 24px; padding: 10px 30px; border-radius: 25px;">
                    {direction}
                </span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;">
                    <p style="color: #888; margin: 0; font-size: 12px;">上涨概率</p>
                    <p style="color: #FF0000; margin: 0; font-size: 28px; font-weight: bold;">{prediction.get('up_probability', 0):.1f}%</p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;">
                    <p style="color: #888; margin: 0; font-size: 12px;">下跌概率</p>
                    <p style="color: #00FF00; margin: 0; font-size: 28px; font-weight: bold;">{prediction.get('down_probability', 0):.1f}%</p>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                <h4 style="color: #888; margin: 0 0 10px 0; font-size: 14px;">支撑位 & 压力位</h4>
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <p style="color: #00FF00; margin: 0;">支撑1: {prediction.get('support1', 0):.2f}</p>
                        <p style="color: #00FF00; margin: 0;">支撑2: {prediction.get('support2', 0):.2f}</p>
                    </div>
                    <div>
                        <p style="color: #FF0000; margin: 0;">压力1: {prediction.get('resistance1', 0):.2f}</p>
                        <p style="color: #FF0000; margin: 0;">压力2: {prediction.get('resistance2', 0):.2f}</p>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                <h4 style="color: #888; margin: 0 0 10px 0; font-size: 14px;">交易建议</h4>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background: {'#FF6B6B' if '买入' in prediction.get('signal', '') else '#26de81' if '卖出' in prediction.get('signal', '') else '#FFD700'}; 
                                   padding: 8px 20px; border-radius: 20px; font-weight: bold;">
                            {prediction.get('signal', '观望')}
                        </span>
                        <span style="margin-left: 15px; color: #888;">风险: {prediction.get('risk_level', '中')}</span>
                    </div>
                    <div>
                        <span style="background: #1976D2; padding: 8px 15px; border-radius: 5px;">
                            建议仓位: {prediction.get('position', '3成')}
                        </span>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <p style="color: #888; margin: 0; font-size: 12px;">目标止盈价</p>
                        <p style="color: #FFD700; margin: 0; font-size: 18px; font-weight: bold;">{prediction.get('target_price', 0):.2f}</p>
                    </div>
                    <div>
                        <p style="color: #888; margin: 0; font-size: 12px;">止损价</p>
                        <p style="color: #FF0000; margin: 0; font-size: 18px; font-weight: bold;">{prediction.get('stop_loss', 0):.2f}</p>
                    </div>
                    <div>
                        <p style="color: #888; margin: 0; font-size: 12px;">模型胜率</p>
                        <p style="color: #26de81; margin: 0; font-size: 18px; font-weight: bold;">{prediction.get('win_rate', 0):.1f}%</p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_fund_flow(fund_data: Dict) -> None:
        """渲染资金流向"""
        main_net = fund_data.get('main_net', 0)
        color = '#FF0000' if main_net > 0 else '#00FF00'
        arrow = '流入' if main_net > 0 else '流出'
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 15px; padding: 20px; margin: 10px 0;">
            <h3 style="color: #888; margin: 0 0 15px 0;">资金流向</h3>
            
            <div style="text-align: center; margin-bottom: 20px;">
                <p style="color: #888; margin: 0; font-size: 14px;">主力{arrow}</p>
                <p style="color: {color}; margin: 0; font-size: 36px; font-weight: bold;">
                    {abs(main_net)/100000000:.2f}亿
                </p>
                <p style="color: #888; margin: 0; font-size: 12px;">
                    占比: {fund_data.get('main_pct', 0):.2f}%
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 10px;">超大单</p>
                    <p style="color: {'#FF0000' if fund_data.get('super_net', 0) > 0 else '#00FF00'}; margin: 0; font-size: 14px;">
                        {fund_data.get('super_net', 0)/10000:.0f}万
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 10px;">大单</p>
                    <p style="color: {'#FF0000' if fund_data.get('big_net', 0) > 0 else '#00FF00'}; margin: 0; font-size: 14px;">
                        {fund_data.get('big_net', 0)/10000:.0f}万
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 10px;">中单</p>
                    <p style="color: {'#FF0000' if fund_data.get('mid_net', 0) > 0 else '#00FF00'}; margin: 0; font-size: 14px;">
                        {fund_data.get('mid_net', 0)/10000:.0f}万
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 10px;">小单</p>
                    <p style="color: {'#FF0000' if fund_data.get('small_net', 0) > 0 else '#00FF00'}; margin: 0; font-size: 14px;">
                        {fund_data.get('small_net', 0)/10000:.0f}万
                    </p>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px; text-align: center;">
                <p style="color: #888; margin: 0; font-size: 12px;">5日主力净流入</p>
                <p style="color: {'#FF0000' if fund_data.get('main_net_5day', 0) > 0 else '#00FF00'}; margin: 0; font-size: 20px; font-weight: bold;">
                    {fund_data.get('main_net_5day', 0)/100000000:.2f}亿
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_news_list(news_list: List[Dict]) -> None:
        """渲染新闻列表"""
        if not news_list:
            st.info("暂无最新消息")
            return
        
        for news in news_list[:10]:
            sentiment = news.get('sentiment', 'neutral')
            tag_color = '#4CAF50' if sentiment == 'positive' else '#F44336' if sentiment == 'negative' else '#9E9E9E'
            tag_text = '利好' if sentiment == 'positive' else '利空' if sentiment == 'negative' else '中性'
            
            with st.expander(f"{news.get('title', '无标题')}", expanded=False):
                st.markdown(f"""
                <div style="padding: 10px;">
                    <span style="background: {tag_color}; padding: 3px 10px; border-radius: 10px; font-size: 12px;">{tag_text}</span>
                    <span style="color: #888; margin-left: 10px; font-size: 12px;">{news.get('time', '')}</span>
                    <span style="color: #888; margin-left: 10px; font-size: 12px;">{news.get('source', '')}</span>
                    <p style="color: #ccc; margin-top: 10px; font-size: 14px;">{news.get('summary', news.get('title', ''))}</p>
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def render_statistics(stats: Dict) -> None:
        """渲染统计面板"""
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 15px; padding: 20px; margin: 10px 0;">
            <h3 style="color: #888; margin: 0 0 20px 0;">核验统计</h3>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 14px;">总预测数</p>
                    <p style="color: #fff; margin: 10px 0 0 0; font-size: 32px; font-weight: bold;">{stats.get('total_predictions', 0)}</p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 14px;">已核验</p>
                    <p style="color: #1976D2; margin: 10px 0 0 0; font-size: 32px; font-weight: bold;">{stats.get('total_verified', 0)}</p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 14px;">预测正确</p>
                    <p style="color: #26de81; margin: 10px 0 0 0; font-size: 32px; font-weight: bold;">{stats.get('correct', 0)}</p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 14px;">综合胜率</p>
                    <p style="color: #FFD700; margin: 10px 0 0 0; font-size: 32px; font-weight: bold;">{stats.get('win_rate', 0):.1f}%</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


class SearchComponents:
    """搜索组件"""
    
    @staticmethod
    def render_search_box(placeholder: str = "输入股票代码、名称或拼音首字母...") -> str:
        """渲染搜索框"""
        return st.text_input("🔍 股票搜索", placeholder=placeholder, key="stock_search")
    
    @staticmethod
    def render_stock_list(stocks: pd.DataFrame, on_select_func=None) -> None:
        """渲染股票列表"""
        if stocks is None or stocks.empty:
            st.info("暂无股票数据")
            return
        
        for idx, row in stocks.iterrows():
            code = row.get('code', '')
            name = row.get('name', row.get('名称', ''))
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}** ({code})")
            with col2:
                if st.button("查看", key=f"btn_{code}"):
                    if on_select_func:
                        on_select_func(code)
            
            st.divider()


# 全局组件实例
charts = ChartComponents()
indicators = IndicatorComponents()
info_components = InfoComponents()
search_components = SearchComponents()
