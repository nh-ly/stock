# -*- coding: utf-8 -*-
"""
数据获取模块
提供AkShare数据接口封装和缓存管理
"""

import akshare as ak
import pandas as pd
import numpy as np
import json
import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

class DataFetcher:
    """数据获取器类"""
    
    def __init__(self):
        self.cache_enabled = True
        self.cache_duration = 300  # 缓存5分钟
    
    def _get_cache_path(self, key: str) -> str:
        """获取缓存文件路径"""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(CACHE_DIR, f"{hash_key}.json")
    
    def _read_cache(self, key: str) -> Optional[Dict]:
        """读取缓存"""
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 检查缓存是否过期
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if (datetime.now() - cache_time).seconds < self.cache_duration:
                    return cache_data['data']
            except:
                pass
        return None
    
    def _write_cache(self, key: str, data: Dict):
        """写入缓存"""
        if not self.cache_enabled:
            return
        
        cache_path = self._get_cache_path(key)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def get_stock_list(self, market: str = 'all') -> pd.DataFrame:
        """获取股票列表"""
        cache_key = f"stock_list_{market}"
        cached = self._read_cache(cache_key)
        
        try:
            # 获取A股股票列表
            df = ak.stock_info_a_code_name()
            
            if df is None or df.empty:
                if cached is not None:
                    print("获取股票列表失败，使用缓存")
                    return pd.DataFrame(cached)
                return pd.DataFrame()
            
            # 过滤ST股和风险警示股
            df = df[~df['name'].str.contains('ST|退市', na=False)]
            
            # 添加市场前缀
            df['code'] = df['code'].apply(lambda x: f"{'sh' if x.startswith(('6', '5')) else 'sz'}{x}")
            
            self._write_cache(cache_key, df.to_dict('records'))
            return df
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            if cached is not None:
                print("使用缓存数据")
                return pd.DataFrame(cached)
            return pd.DataFrame()
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情"""
        # 移除市场前缀
        code = stock_code.replace('sh', '').replace('sz', '')
        cache_key = f"realtime_{code}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == code]
            
            if stock_data.empty:
                return None
            
            result = {
                'code': code,
                'name': stock_data.iloc[0]['名称'],
                'price': float(stock_data.iloc[0]['最新价']),
                'change': float(stock_data.iloc[0]['涨跌幅']),
                'volume': float(stock_data.iloc[0]['成交量']),
                'amount': float(stock_data.iloc[0]['成交额']),
                'open': float(stock_data.iloc[0]['今开']),
                'high': float(stock_data.iloc[0]['最高']),
                'low': float(stock_data.iloc[0]['最低']),
                'close_prev': float(stock_data.iloc[0]['昨收']),
                'volume_ratio': float(stock_data.iloc[0]['量比']),
                'turnover': float(stock_data.iloc[0]['换手率']),
                'amplitude': float(stock_data.iloc[0]['振幅']),
                'market_cap': float(stock_data.iloc[0]['总市值']),
                'float_cap': float(stock_data.iloc[0]['流通市值']),
                'pe': float(stock_data.iloc[0]['市盈率-动态']) if pd.notna(stock_data.iloc[0]['市盈率-动态']) else None,
                'pb': float(stock_data.iloc[0]['市净率']) if pd.notna(stock_data.iloc[0]['市净率']) else None,
                'timestamp': datetime.now().isoformat()
            }
            
            self._write_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"获取实时行情失败 {stock_code}: {e}")
            return None
    
    def get_historical_data(self, stock_code: str, period: str = 'daily', 
                           adjust: str = 'qfq') -> Optional[pd.DataFrame]:
        """获取历史K线数据"""
        # 移除市场前缀
        code = stock_code.replace('sh', '').replace('sz', '')
        cache_key = f"history_{code}_{period}_{adjust}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return pd.DataFrame(cached)
        
        try:
            if period == 'daily':
                df = ak.stock_zh_a_hist(symbol=code, period='daily', adjust=adjust)
            elif period == 'weekly':
                df = ak.stock_zh_a_hist(symbol=code, period='weekly', adjust=adjust)
            elif period == 'monthly':
                df = ak.stock_zh_a_hist(symbol=code, period='monthly', adjust=adjust)
            elif period == '60min':
                df = ak.stock_zh_a_hist(symbol=code, period='60min', adjust=adjust)
            elif period == '30min':
                df = ak.stock_zh_a_hist(symbol=code, period='30min', adjust=adjust)
            elif period == '15min':
                df = ak.stock_zh_a_hist(symbol=code, period='15min', adjust=adjust)
            else:  # 5min or 1min
                df = ak.stock_zh_a_hist(symbol=code, period='5', adjust=adjust)
            
            if df is not None and not df.empty:
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                })
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                self._write_cache(cache_key, df.to_dict('records'))
                return df
        except Exception as e:
            print(f"获取历史数据失败 {stock_code} {period}: {e}")
        return None
    
    def get_minute_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取分时数据"""
        code = stock_code.replace('sh', '').replace('sz', '')
        cache_key = f"minute_{code}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return pd.DataFrame(cached)
        
        try:
            df = ak.stock_zh_a_hist(symbol=code, period='1', adjust='qfq')
            if df is not None and not df.empty:
                df = df.tail(241)  # 取最近一天的分钟数据
                df = df.rename(columns={
                    '日期': 'time',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume'
                })
                
                self._write_cache(cache_key, df.to_dict('records'))
                return df
        except Exception as e:
            print(f"获取分时数据失败 {stock_code}: {e}")
        return None
    
    def get_capital_flow(self, stock_code: str) -> Optional[Dict]:
        """获取资金流向"""
        code = stock_code.replace('sh', '').replace('sz', '')
        cache_key = f"capital_{code}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            # 获取主力资金流向
            df = ak.stock_individual_fund_flow(stock=code, market='sh')
            if df is None or df.empty:
                df = ak.stock_individual_fund_flow(stock=code, market='sz')
            
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                result = {
                    'date': str(latest.get('日期', '')),
                    'main_net': float(latest.get('主力净流入', 0)),
                    'main_pct': float(latest.get('主力净流入占比', 0)),
                    'super_net': float(latest.get('超大单净流入', 0)),
                    'big_net': float(latest.get('大单净流入', 0)),
                    'mid_net': float(latest.get('中单净流入', 0)),
                    'small_net': float(latest.get('小单净流入', 0)),
                }
                
                # 获取5日资金流向
                five_day = df.tail(5)
                result['main_net_5day'] = five_day['主力净流入'].sum() if '主力净流入' in five_day.columns else 0
                
                self._write_cache(cache_key, result)
                return result
        except Exception as e:
            print(f"获取资金流向失败 {stock_code}: {e}")
        return {'main_net': 0, 'main_pct': 0, 'main_net_5day': 0}
    
    def get_stock_profile(self, stock_code: str) -> Optional[Dict]:
        """获取股票基本面信息"""
        code = stock_code.replace('sh', '').replace('sz', '')
        cache_key = f"profile_{code}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            # 获取股票基本信息
            df = ak.stock_individual_info_em(symbol=code)
            if df is not None and not df.empty:
                info = dict(zip(df['item'], df['value']))
                
                result = {
                    'name': info.get('股票简称', ''),
                    'industry': info.get('行业', ''),
                    'listing_date': info.get('上市时间', ''),
                    'total_shares': info.get('总股本', ''),
                    'float_shares': info.get('流通股本', ''),
                    'eps': info.get('每股收益', ''),
                    'bps': info.get('每股净资产', ''),
                }
                
                self._write_cache(cache_key, result)
                return result
        except Exception as e:
            print(f"获取股票基本信息失败 {stock_code}: {e}")
        return {}
    
    def get_news(self, stock_code: str) -> List[Dict]:
        """获取个股新闻公告"""
        code = stock_code.replace('sh', '').replace('sz', '')
        cache_key = f"news_{code}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            news_list = []
            
            # 获取个股新闻
            try:
                df = ak.stock_news_em(symbol=code)
                if df is not None and not df.empty:
                    for _, row in df.head(10).iterrows():
                        news_list.append({
                            'title': str(row.get('新闻标题', '')),
                            'time': str(row.get('发布时间', '')),
                            'source': str(row.get('文章来源', '')),
                            'type': 'news'
                        })
            except:
                pass
            
            # 获取个股公告
            try:
                df = ak.stock_announcement(symbol=code, date='20240101')
                if df is not None and not df.empty:
                    for _, row in df.head(5).iterrows():
                        news_list.append({
                            'title': str(row.get('公告标题', '')),
                            'time': str(row.get('发布时间', '')),
                            'source': '公司公告',
                            'type': 'announcement'
                        })
            except:
                pass
            
            self._write_cache(cache_key, news_list)
            return news_list
        except Exception as e:
            print(f"获取新闻失败 {stock_code}: {e}")
        return []
    
    def get_index_data(self, index_code: str = '000001') -> Optional[pd.DataFrame]:
        """获取指数数据"""
        cache_key = f"index_{index_code}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return pd.DataFrame(cached)
        
        try:
            if index_code == '000001':
                df = ak.stock_zh_index_daily(symbol="sh000001")
            elif index_code == '399001':
                df = ak.stock_zh_index_daily(symbol="sz399001")
            elif index_code == '399006':
                df = ak.stock_zh_index_daily(symbol="sz399006")
            else:
                return None
            
            if df is not None and not df.empty:
                self._write_cache(cache_key, df.to_dict('records'))
                return df
        except Exception as e:
            print(f"获取指数数据失败 {index_code}: {e}")
        return None
    
    def get_market_heatmap(self) -> Optional[pd.DataFrame]:
        """获取市场涨跌统计"""
        cache_key = "market_heatmap"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return pd.DataFrame(cached)
        
        try:
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                # 统计涨跌
                up_count = len(df[df['涨跌幅'] > 0])
                down_count = len(df[df['涨跌幅'] < 0])
                flat_count = len(df[df['涨跌幅'] == 0])
                
                result = df[['代码', '名称', '最新价', '涨跌幅']].to_dict('records')
                result_meta = {'up': up_count, 'down': down_count, 'flat': flat_count, 'total': len(df)}
                
                self._write_cache(cache_key, result)
                return pd.DataFrame(result)
        except Exception as e:
            print(f"获取市场热力图失败: {e}")
        return None
    
    def clear_cache(self):
        """清空缓存"""
        import shutil
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR, exist_ok=True)

# 全局数据获取器实例
data_fetcher = DataFetcher()
