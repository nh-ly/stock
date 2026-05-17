# -*- coding: utf-8 -*-
"""
UI组件模块 - 专业版
提供专业级的K线图、分时图、技术指标、资金流向、龙虎榜、板块轮动等可视化组件
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
    """专业图表组件"""
    
    @staticmethod
    def render_kline_chart(data: pd.DataFrame, period: str = '日线', indicators: Dict = None) -> Optional[go.Figure]:
        """渲染专业K线图"""
        if data is None or data.empty or len(data) < 2:
            return None
        
        df = data.tail(120).copy()
        
        # 创建子图
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.55, 0.225, 0.225],
            subplot_titles=('K线图', '成交量', 'MACD'),
            specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # 颜色配置
        up_color = '#FF4D4F'
        down_color = '#52C41A'
        
        # K线图
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='K线',
                increasing_line_color=up_color,
                decreasing_line_color=down_color,
                increasing_fillcolor=up_color,
                decreasing_fillcolor=down_color,
                increasing_line_width=1.5,
                decreasing_line_width=1.5
            ),
            row=1, col=1
        )
        
        # 添加技术指标
        if indicators:
            if indicators.get('ma5', True) and 'ma5' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ma5'], name='MA5', 
                                         line=dict(color='#FF9800', width=1.5),
                                         opacity=0.8), row=1, col=1)
            if indicators.get('ma10', True) and 'ma10' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], name='MA10', 
                                         line=dict(color='#2196F3', width=1.5),
                                         opacity=0.8), row=1, col=1)
            if indicators.get('ma20', True) and 'ma20' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], name='MA20', 
                                         line=dict(color='#9C27B0', width=2),
                                         opacity=0.9), row=1, col=1)
            if indicators.get('ma60', False) and 'ma60' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['ma60'], name='MA60', 
                                         line=dict(color='#607D8B', width=1.5),
                                         opacity=0.7, dash='dash'), row=1, col=1)
            
            if indicators.get('boll', True) and 'boll_upper' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['boll_upper'], name='BOLL上轨', 
                                         line=dict(color='#E91E63', width=1, dash='dot'),
                                         opacity=0.6), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['date'], y=df['boll_mid'], name='BOLL中轨', 
                                         line=dict(color='#E91E63', width=1),
                                         opacity=0.7), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['date'], y=df['boll_lower'], name='BOLL下轨', 
                                         line=dict(color='#E91E63', width=1, dash='dot'),
                                         opacity=0.6), row=1, col=1)
        
        # 成交量
        volume_colors = [up_color if c >= o else down_color for c, o in zip(df['close'], df['open'])]
        fig.add_trace(
            go.Bar(x=df['date'], y=df['volume'], name='成交量', 
                   marker_color=volume_colors, opacity=0.8),
            row=2, col=1
        )
        
        # MACD
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            macd_colors = [up_color if v >= 0 else down_color for v in df['macd_hist']]
            fig.add_trace(
                go.Bar(x=df['date'], y=df['macd_hist'], name='MACD柱', 
                       marker_color=macd_colors, opacity=0.7),
                row=3, col=1
            )
            fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', 
                                     line=dict(color='#FF00FF', width=1.5)), row=3, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', 
                                     line=dict(color='#00FFFF', width=1.5)), row=3, col=1)
        
        # 布局配置
        fig.update_layout(
            template='plotly_dark',
            height=700,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                       bgcolor='rgba(0,0,0,0)'),
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=40, b=10)
        )
        
        # 坐标轴配置
        fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)', 
                        zerolinecolor='rgba(255,255,255,0.2)')
        fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)',
                        zerolinecolor='rgba(255,255,255,0.2)')
        
        return fig
    
    @staticmethod
    def render_minute_chart(data: pd.DataFrame) -> Optional[go.Figure]:
        """渲染专业分时图"""
        if data is None or data.empty:
            return None
        
        fig = go.Figure()
        
        # 分时线
        fig.add_trace(go.Scatter(
            x=data['time'] if 'time' in data.columns else data.index,
            y=data['close'],
            mode='lines',
            name='分时',
            line=dict(color='#FF4D4F', width=2),
            fill='tonexty',
            fillcolor='rgba(255,77,79,0.1)'
        ))
        
        # 成交量
        fig.add_trace(go.Bar(
            x=data['time'] if 'time' in data.columns else data.index,
            y=data['volume'],
            name='成交量',
            marker_color='rgba(255,77,79,0.5)',
            yaxis='y2'
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=400,
            showlegend=True,
            hovermode='x unified',
            xaxis_rangeslider_visible=False,
            yaxis=dict(title='价格', side='left'),
            yaxis2=dict(title='成交量', side='right', overlaying='y'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    @staticmethod
    def render_capital_flow_chart(data: Dict) -> Optional[go.Figure]:
        """渲染专业资金流向图"""
        if not data:
            return None
        
        labels = ['超大单', '大单', '中单', '小单']
        values = [
            data.get('super_net', 0),
            data.get('big_net', 0),
            data.get('mid_net', 0),
            data.get('small_net', 0)
        ]
        
        colors = ['#FF4D4F' if v > 0 else '#52C41A' for v in values]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f'{v/100000000:.2f}亿' if abs(v)>=100000000 else f'{v/10000:.0f}万' for v in values],
            textposition='outside',
            textfont=dict(size=12, color='white'),
            width=0.6
        ))
        
        fig.update_layout(
            title=dict(text='资金流向分布', x=0.5, font=dict(size=16)),
            template='plotly_dark',
            height=350,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        fig.update_yaxes(title='净额')
        
        return fig
    
    @staticmethod
    def render_fund_trend_chart(data: pd.DataFrame) -> Optional[go.Figure]:
        """渲染资金趋势图"""
        if data is None or data.empty:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['date'] if 'date' in data.columns else data.index,
            y=data.get('main_net', data['close'] if 'close' in data.columns else []),
            mode='lines+markers',
            name='主力净流入',
            fill='tozeroy',
            line=dict(color='#FF4D4F', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=300,
            showlegend=True,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    @staticmethod
    def render_sector_performance_chart(data: pd.DataFrame) -> Optional[go.Figure]:
        """渲染板块涨跌幅排行图"""
        if data is None or data.empty:
            return None
        
        df = data.head(20).copy()
        
        colors = ['#FF4D4F' if x > 0 else '#52C41A' for x in df.iloc[:, 1] if len(df.columns) > 1]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df.iloc[:, 0],
            x=df.iloc[:, 1],
            orientation='h',
            marker_color=colors,
            text=[f'{x:.2f}%' for x in df.iloc[:, 1]],
            textposition='outside'
        ))
        
        fig.update_layout(
            title=dict(text='板块涨跌幅排行', x=0.5),
            template='plotly_dark',
            height=500,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    @staticmethod
    def render_northbound_flow_chart(data: pd.DataFrame) -> Optional[go.Figure]:
        """渲染北向资金流向图"""
        if data is None or data.empty:
            return None
        
        df = data.tail(30).copy()
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df.iloc[:, 0],
            y=df.iloc[:, 1],
            name='北向资金',
            marker_color=['#FF4D4F' if x > 0 else '#52C41A' for x in df.iloc[:, 1]]
        ))
        
        fig.update_layout(
            title=dict(text='北向资金近30日流向', x=0.5),
            template='plotly_dark',
            height=350,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    @staticmethod
    def render_market_heatmap(data: Dict) -> Optional[go.Figure]:
        """渲染市场涨跌热力图"""
        if not data:
            return None
        
        labels = ['上涨', '平盘', '下跌', '涨停', '跌停']
        values = [
            data.get('up', 0),
            data.get('flat', 0),
            data.get('down', 0),
            data.get('limit_up', 0),
            data.get('limit_down', 0)
        ]
        colors = ['#FF4D4F', '#FAAD14', '#52C41A', '#F5222D', '#389E0D']
        
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            textinfo='label+percent+value',
            textposition='inside',
            hole=0.4
        ))
        
        fig.update_layout(
            title=dict(text='市场涨跌分布', x=0.5),
            template='plotly_dark',
            height=400,
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def render_win_rate_gauge(win_rate: float, title: str = '胜率') -> go.Figure:
        """渲染胜率仪表盘"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=win_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 16}},
            number={'suffix': '%', 'font': {'size': 28}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "#1890FF"},
                'steps': [
                    {'range': [0, 40], 'color': "#FF4D4F"},
                    {'range': [40, 60], 'color': "#FAAD14"},
                    {'range': [60, 80], 'color': "#52C41A"},
                    {'range': [80, 100], 'color': "#13C2C2"}
                ],
                'threshold': {
                    'line': {'color': "#F5222D", 'width': 4},
                    'thickness': 0.8,
                    'value': win_rate
                }
            }
        ))
        
        fig.update_layout(height=250, template='plotly_dark')
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
            'RSI': round(latest.get('rsi', 50), 2) if pd.notna(latest.get('rsi')) else 50,
            '量比': round(latest.get('vol_ratio', 1), 2) if pd.notna(latest.get('vol_ratio')) else 1
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
        
        # MA金叉死叉
        if pd.notna(latest.get('ma5')) and pd.notna(latest.get('ma20')):
            if latest['ma5'] > latest['ma20'] and prev['ma5'] <= prev['ma20']:
                tags.append('🚀 MA金叉')
            elif latest['ma5'] < latest['ma20'] and prev['ma5'] >= prev['ma20']:
                tags.append('⚠️ MA死叉')
        
        # KDJ信号
        if pd.notna(latest.get('kdj_k')) and pd.notna(latest.get('kdj_d')):
            if latest['kdj_k'] > latest['kdj_d'] and prev['kdj_k'] <= prev['kdj_d']:
                tags.append('🎯 KDJ金叉')
            elif latest['kdj_k'] < latest['kdj_d'] and prev['kdj_k'] >= prev['kdj_d']:
                tags.append('💧 KDJ死叉')
            
            if latest['kdj_k'] > 80:
                tags.append('🔥 KDJ超买')
            elif latest['kdj_k'] < 20:
                tags.append('❄️ KDJ超卖')
        
        # MACD信号
        if pd.notna(latest.get('macd')) and pd.notna(latest.get('macd_signal')):
            if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                tags.append('📈 MACD金叉')
            elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                tags.append('📉 MACD死叉')
        
        # RSI信号
        if pd.notna(latest.get('rsi')):
            if latest['rsi'] > 70:
                tags.append('⚡ RSI超买')
            elif latest['rsi'] < 30:
                tags.append('🌟 RSI超卖')
        
        # 均线排列
        if pd.notna(latest.get('ma5')) and pd.notna(latest.get('ma20')) and pd.notna(latest.get('ma60')):
            if latest['ma5'] > latest['ma20'] > latest['ma60']:
                tags.append('💪 多头排列')
            elif latest['ma5'] < latest['ma20'] < latest['ma60']:
                tags.append('😰 空头排列')
        
        # 布林带信号
        if pd.notna(latest.get('close')) and pd.notna(latest.get('boll_upper')) and pd.notna(latest.get('boll_lower')):
            if latest['close'] > latest['boll_upper']:
                tags.append('💥 突破上轨')
            elif latest['close'] < latest['boll_lower']:
                tags.append('🎁 跌破下轨')
        
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
            market_cap = quote.get('market_cap', 0)
            float_cap = quote.get('float_cap', 0)
            st.metric("总市值", f"{market_cap/100000000:.2f}亿" if market_cap else 'N/A')
            st.metric("流通市值", f"{float_cap/100000000:.2f}亿" if float_cap else 'N/A')
        with col3:
            pe = quote.get('pe')
            pb = quote.get('pb')
            st.metric("市盈率(PE)", f"{pe:.2f}" if pe else 'N/A')
            st.metric("市净率(PB)", f"{pb:.2f}" if pb else 'N/A')
        with col4:
            turnover = quote.get('turnover', 0)
            volume_ratio = quote.get('volume_ratio', 0)
            st.metric("换手率", f"{turnover:.2f}%" if turnover else 'N/A')
            st.metric("量比", f"{volume_ratio:.2f}" if volume_ratio else 'N/A')
    
    @staticmethod
    def render_realtime_quote(quote: Dict) -> None:
        """渲染实时行情"""
        price = quote.get('price', 0)
        change = quote.get('change', 0)
        prev_close = quote.get('close_prev', price)
        
        color = '#FF4D4F' if change > 0 else '#52C41A' if change < 0 else '#888888'
        arrow = '▲' if change > 0 else '▼' if change < 0 else '─'
        
        change_value = price - prev_close
        
        st.markdown(f"""
        <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <h1 style="color: {color}; margin: 0; font-size: 56px; font-weight: 800; letter-spacing: -1px;">
                {price:.2f}
            </h1>
            <p style="color: {color}; margin: 8px 0; font-size: 24px; font-weight: 600;">
                {arrow} {abs(change_value):.2f} ({abs(change):.2f}%)
            </p>
            <div style="display: flex; justify-content: center; gap: 30px; margin-top: 15px; padding: 15px; 
                        background: rgba(255,255,255,0.05); border-radius: 10px;">
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 12px;">今开</div>
                    <div style="color: #fff; font-size: 18px; font-weight: 600;">{quote.get('open', 0):.2f}</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 12px;">最高</div>
                    <div style="color: #FF4D4F; font-size: 18px; font-weight: 600;">{quote.get('high', 0):.2f}</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 12px;">最低</div>
                    <div style="color: #52C41A; font-size: 18px; font-weight: 600;">{quote.get('low', 0):.2f}</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 12px;">昨收</div>
                    <div style="color: #fff; font-size: 18px; font-weight: 600;">{prev_close:.2f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_prediction_result(prediction: Dict) -> None:
        """渲染预测结果"""
        direction = prediction.get('direction', '区间震荡')
        
        direction_colors = {
            '看涨': '#FF4D4F',
            '看跌': '#52C41A',
            '区间震荡': '#FAAD14'
        }
        
        color = direction_colors.get(direction, '#FAAD14')
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border-radius: 15px; padding: 25px; margin: 10px 0;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="text-align: center; margin-bottom: 20px;">
                <span style="background: {color}; padding: 12px 35px; border-radius: 25px; 
                             font-size: 22px; font-weight: 700; color: white;
                             box-shadow: 0 4px 15px {color}40;">
                    {direction}
                </span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;
                            text-align: center; border-left: 3px solid #FF4D4F;">
                    <p style="color: #888; margin: 0; font-size: 13px;">上涨概率</p>
                    <p style="color: #FF4D4F; margin: 8px 0 0 0; font-size: 32px; font-weight: 800;">
                        {prediction.get('up_probability', 0):.1f}%
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;
                            text-align: center; border-left: 3px solid #52C41A;">
                    <p style="color: #888; margin: 0; font-size: 13px;">下跌概率</p>
                    <p style="color: #52C41A; margin: 8px 0 0 0; font-size: 32px; font-weight: 800;">
                        {prediction.get('down_probability', 0):.1f}%
                    </p>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 18px; background: rgba(255,255,255,0.05); 
                        border-radius: 12px;">
                <h4 style="color: #888; margin: 0 0 12px 0; font-size: 14px;">支撑位 & 压力位</h4>
                <div style="display: flex; justify-content: space-around;">
                    <div style="text-align: center;">
                        <div style="color: #52C41A; font-size: 12px;">支撑1</div>
                        <div style="color: #52C41A; font-size: 20px; font-weight: 700;">
                            {prediction.get('support1', 0):.2f}
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #52C41A; font-size: 12px;">支撑2</div>
                        <div style="color: #52C41A; font-size: 20px; font-weight: 700;">
                            {prediction.get('support2', 0):.2f}
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #FF4D4F; font-size: 12px;">压力1</div>
                        <div style="color: #FF4D4F; font-size: 20px; font-weight: 700;">
                            {prediction.get('resistance1', 0):.2f}
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #FF4D4F; font-size: 12px;">压力2</div>
                        <div style="color: #FF4D4F; font-size: 20px; font-weight: 700;">
                            {prediction.get('resistance2', 0):.2f}
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 18px; background: rgba(255,255,255,0.05); 
                        border-radius: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background: {color}; padding: 8px 20px; border-radius: 20px; 
                                     font-weight: 700; color: white; font-size: 15px;">
                            {prediction.get('signal', '观望')}
                        </span>
                        <span style="margin-left: 15px; color: #888; font-size: 14px;">
                            风险等级: {prediction.get('risk_level', '中')}
                        </span>
                    </div>
                    <div>
                        <span style="background: #1890FF; padding: 8px 15px; border-radius: 8px;
                                     color: white; font-weight: 600;">
                            建议仓位: {prediction.get('position', '3成')}
                        </span>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 18px; background: rgba(255,255,255,0.05); 
                        border-radius: 12px;">
                <div style="display: flex; justify-content: space-around;">
                    <div style="text-align: center;">
                        <p style="color: #888; margin: 0; font-size: 12px;">目标止盈</p>
                        <p style="color: #FAAD14; margin: 5px 0 0 0; font-size: 22px; font-weight: 700;">
                            {prediction.get('target_price', 0):.2f}
                        </p>
                    </div>
                    <div style="text-align: center;">
                        <p style="color: #888; margin: 0; font-size: 12px;">止损价位</p>
                        <p style="color: #FF4D4F; margin: 5px 0 0 0; font-size: 22px; font-weight: 700;">
                            {prediction.get('stop_loss', 0):.2f}
                        </p>
                    </div>
                    <div style="text-align: center;">
                        <p style="color: #888; margin: 0; font-size: 12px;">历史胜率</p>
                        <p style="color: #52C41A; margin: 5px 0 0 0; font-size: 22px; font-weight: 700;">
                            {prediction.get('win_rate', 0):.1f}%
                        </p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_fund_flow(fund_data: Dict) -> None:
        """渲染资金流向"""
        main_net = fund_data.get('main_net', 0)
        color = '#FF4D4F' if main_net > 0 else '#52C41A'
        arrow = '净流入' if main_net > 0 else '净流出'
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border-radius: 15px; padding: 25px; margin: 10px 0;">
            <h3 style="color: #888; margin: 0 0 20px 0; font-size: 16px;">💵 资金流向</h3>
            
            <div style="text-align: center; margin-bottom: 25px; padding: 20px;
                        background: rgba(255,255,255,0.05); border-radius: 12px;">
                <p style="color: #888; margin: 0; font-size: 14px;">主力{arrow}</p>
                <p style="color: {color}; margin: 8px 0 0 0; font-size: 36px; font-weight: 800;">
                    {abs(main_net)/100000000:.2f}亿
                </p>
                <p style="color: #888; margin: 5px 0 0 0; font-size: 13px;">
                    占比: {fund_data.get('main_pct', 0):.2f}%
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; 
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 11px;">超大单</p>
                    <p style="color: {'#FF4D4F' if fund_data.get('super_net', 0) > 0 else '#52C41A'}; 
                       margin: 8px 0 0 0; font-size: 16px; font-weight: 700;">
                        {fund_data.get('super_net', 0)/10000:.0f}万
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; 
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 11px;">大单</p>
                    <p style="color: {'#FF4D4F' if fund_data.get('big_net', 0) > 0 else '#52C41A'}; 
                       margin: 8px 0 0 0; font-size: 16px; font-weight: 700;">
                        {fund_data.get('big_net', 0)/10000:.0f}万
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; 
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 11px;">中单</p>
                    <p style="color: {'#FF4D4F' if fund_data.get('mid_net', 0) > 0 else '#52C41A'}; 
                       margin: 8px 0 0 0; font-size: 16px; font-weight: 700;">
                        {fund_data.get('mid_net', 0)/10000:.0f}万
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; 
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 11px;">小单</p>
                    <p style="color: {'#FF4D4F' if fund_data.get('small_net', 0) > 0 else '#52C41A'}; 
                       margin: 8px 0 0 0; font-size: 16px; font-weight: 700;">
                        {fund_data.get('small_net', 0)/10000:.0f}万
                    </p>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.05); 
                        border-radius: 10px; text-align: center;">
                <p style="color: #888; margin: 0; font-size: 12px;">近5日主力累计</p>
                <p style="color: {'#FF4D4F' if fund_data.get('main_net_5day', 0) > 0 else '#52C41A'}; 
                   margin: 8px 0 0 0; font-size: 24px; font-weight: 700;">
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
        
        for news in news_list[:15]:
            sentiment = news.get('sentiment', 'neutral')
            tag_colors = {
                'positive': '#52C41A',
                'negative': '#FF4D4F',
                'neutral': '#8C8C8C'
            }
            tag_texts = {
                'positive': '利好',
                'negative': '利空',
                'neutral': '中性'
            }
            type_icons = {
                'news': '📰',
                'announcement': '📢'
            }
            
            color = tag_colors.get(sentiment, '#8C8C8C')
            tag = tag_texts.get(sentiment, '中性')
            icon = type_icons.get(news.get('type', 'news'), '📰')
            
            with st.expander(f"{icon} {news.get('title', '无标题')}", expanded=False):
                st.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="margin-bottom: 10px;">
                        <span style="background: {color}; padding: 4px 12px; border-radius: 15px; 
                                     font-size: 12px; color: white; font-weight: 600;">
                            {tag}
                        </span>
                        <span style="color: #888; margin-left: 12px; font-size: 13px;">
                            {news.get('time', '')}
                        </span>
                        <span style="color: #888; margin-left: 12px; font-size: 13px;">
                            {news.get('source', '')}
                        </span>
                    </div>
                    <p style="color: #d9d9d9; font-size: 15px; line-height: 1.6;">
                        {news.get('summary', news.get('title', ''))}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def render_statistics(stats: Dict) -> None:
        """渲染统计面板"""
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border-radius: 15px; padding: 25px; margin: 10px 0;">
            <h3 style="color: #888; margin: 0 0 25px 0; font-size: 16px;">📊 核验统计</h3>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
                <div style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 12px;
                            text-align: center; border-top: 3px solid #1890FF;">
                    <p style="color: #888; margin: 0; font-size: 13px;">总预测数</p>
                    <p style="color: #fff; margin: 10px 0 0 0; font-size: 36px; font-weight: 800;">
                        {stats.get('total_predictions', 0)}
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 12px;
                            text-align: center; border-top: 3px solid #1890FF;">
                    <p style="color: #888; margin: 0; font-size: 13px;">已核验</p>
                    <p style="color: #1890FF; margin: 10px 0 0 0; font-size: 36px; font-weight: 800;">
                        {stats.get('total_verified', 0)}
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 12px;
                            text-align: center; border-top: 3px solid #52C41A;">
                    <p style="color: #888; margin: 0; font-size: 13px;">预测正确</p>
                    <p style="color: #52C41A; margin: 10px 0 0 0; font-size: 36px; font-weight: 800;">
                        {stats.get('correct', 0)}
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 12px;
                            text-align: center; border-top: 3px solid #FAAD14;">
                    <p style="color: #888; margin: 0; font-size: 13px;">综合胜率</p>
                    <p style="color: #FAAD14; margin: 10px 0 0 0; font-size: 36px; font-weight: 800;">
                        {stats.get('win_rate', 0):.1f}%
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_market_overview(market_data: Dict) -> None:
        """渲染市场概览"""
        if not market_data:
            return
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border-radius: 15px; padding: 25px; margin: 10px 0;">
            <h3 style="color: #888; margin: 0 0 20px 0; font-size: 16px;">🌍 市场概览</h3>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 13px;">上涨</p>
                    <p style="color: #FF4D4F; margin: 10px 0 0 0; font-size: 32px; font-weight: 800;">
                        {market_data.get('up', 0)}
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 13px;">平盘</p>
                    <p style="color: #FAAD14; margin: 10px 0 0 0; font-size: 32px; font-weight: 800;">
                        {market_data.get('flat', 0)}
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 13px;">下跌</p>
                    <p style="color: #52C41A; margin: 10px 0 0 0; font-size: 32px; font-weight: 800;">
                        {market_data.get('down', 0)}
                    </p>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px;">
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 13px;">涨停</p>
                    <p style="color: #F5222D; margin: 10px 0 0 0; font-size: 28px; font-weight: 800;">
                        {market_data.get('limit_up', 0)}
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px;
                            text-align: center;">
                    <p style="color: #888; margin: 0; font-size: 13px;">跌停</p>
                    <p style="color: #389E0D; margin: 10px 0 0 0; font-size: 28px; font-weight: 800;">
                        {market_data.get('limit_down', 0)}
                    </p>
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
