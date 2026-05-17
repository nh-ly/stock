# -*- coding: utf-8 -*-
"""
预测验证与胜率统计模块
负责记录每日预测、自动核验、生成胜率报表
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICT_DIR = os.path.join(BASE_DIR, 'data', 'predictions')
VERIFY_DIR = os.path.join(BASE_DIR, 'data', 'verification')
os.makedirs(PREDICT_DIR, exist_ok=True)
os.makedirs(VERIFY_DIR, exist_ok=True)


class PredictionRecorder:
    """预测记录器"""
    
    def __init__(self):
        self.predict_file = os.path.join(PREDICT_DIR, 'predictions.json')
        self.verify_file = os.path.join(VERIFY_DIR, 'verification.json')
        self.stats_file = os.path.join(VERIFY_DIR, 'statistics.json')
    
    def save_prediction(self, prediction_data: Dict) -> bool:
        """保存单条预测记录"""
        try:
            predictions = self.load_predictions()
            
            record = {
                'id': len(predictions) + 1,
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'stock_code': prediction_data.get('stock_code', ''),
                'stock_name': prediction_data.get('stock_name', ''),
                'model': prediction_data.get('model', ''),
                'direction': prediction_data.get('direction', ''),
                'up_probability': prediction_data.get('up_probability', 0),
                'down_probability': prediction_data.get('down_probability', 0),
                'support1': prediction_data.get('support1', 0),
                'support2': prediction_data.get('support2', 0),
                'resistance1': prediction_data.get('resistance1', 0),
                'resistance2': prediction_data.get('resistance2', 0),
                'target_price': prediction_data.get('target_price', 0),
                'stop_loss': prediction_data.get('stop_loss', 0),
                'signal': prediction_data.get('signal', ''),
                'position': prediction_data.get('position', ''),
                'risk_level': prediction_data.get('risk_level', ''),
                'analysis': prediction_data.get('analysis', ''),
                'verified': False,
                'verify_result': None,
                'verify_date': None,
                'actual_close': None,
                'actual_change': None
            }
            
            predictions.append(record)
            
            with open(self.predict_file, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存预测记录失败: {e}")
            return False
    
    def load_predictions(self) -> List[Dict]:
        """加载所有预测记录"""
        if os.path.exists(self.predict_file):
            try:
                with open(self.predict_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def get_predictions_by_stock(self, stock_code: str) -> List[Dict]:
        """获取指定股票的所有预测"""
        predictions = self.load_predictions()
        return [p for p in predictions if p.get('stock_code') == stock_code]
    
    def get_predictions_by_model(self, model: str) -> List[Dict]:
        """获取指定模型的所有预测"""
        predictions = self.load_predictions()
        return [p for p in predictions if p.get('model') == model]
    
    def get_predictions_by_date(self, date: str) -> List[Dict]:
        """获取指定日期的所有预测"""
        predictions = self.load_predictions()
        return [p for p in predictions if p.get('date') == date]
    
    def get_unverified_predictions(self) -> List[Dict]:
        """获取未核验的预测"""
        predictions = self.load_predictions()
        return [p for p in predictions if not p.get('verified', False)]


class PredictionVerifier:
    """预测核验器"""
    
    def __init__(self):
        self.recorder = PredictionRecorder()
        self.verify_file = os.path.join(VERIFY_DIR, 'verification.json')
    
    def verify_prediction(self, prediction_id: int, actual_data: Dict) -> Dict:
        """核验单条预测"""
        predictions = self.recorder.load_predictions()
        
        target_pred = None
        pred_index = -1
        
        for i, pred in enumerate(predictions):
            if pred.get('id') == prediction_id:
                target_pred = pred
                pred_index = i
                break
        
        if target_pred is None:
            return {'success': False, 'message': '预测记录不存在'}
        
        actual_close = actual_data.get('close', 0)
        actual_change = actual_data.get('change', 0)
        pred_price = target_pred.get('target_price', 0)
        pred_direction = target_pred.get('direction', '')
        pred_support1 = target_pred.get('support1', 0)
        pred_support2 = target_pred.get('support2', 0)
        pred_resistance1 = target_pred.get('resistance1', 0)
        pred_resistance2 = target_pred.get('resistance2', 0)
        
        # 方向核验
        direction_correct = False
        if pred_direction == "看涨" and actual_change > 0:
            direction_correct = True
        elif pred_direction == "看跌" and actual_change < 0:
            direction_correct = True
        elif pred_direction == "区间震荡" and abs(actual_change) < 2:
            direction_correct = True
        
        # 价格区间核验
        price_correct = False
        if pred_price > 0:
            price_diff = abs(actual_close - pred_price) / pred_price
            price_correct = price_diff < 0.05  # 5%误差内
        
        # 支撑压力位核验
        support_correct = actual_close >= pred_support2 if pred_support2 > 0 else None
        resistance_correct = actual_close <= pred_resistance2 if pred_resistance2 > 0 else None
        
        # 综合结果
        overall_correct = direction_correct  # 主要看方向
        
        # 判定等级
        if direction_correct and price_correct:
            result = "完全正确"
            score = 100
        elif direction_correct:
            result = "方向正确"
            score = 70
        else:
            result = "预测错误"
            score = 30
        
        # 更新预测记录
        predictions[pred_index]['verified'] = True
        predictions[pred_index]['verify_result'] = result
        predictions[pred_index]['verify_date'] = datetime.now().strftime('%Y-%m-%d')
        predictions[pred_index]['actual_close'] = actual_close
        predictions[pred_index]['actual_change'] = actual_change
        
        # 保存更新后的记录
        with open(self.recorder.predict_file, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
        
        # 添加核验记录
        verify_record = {
            'id': prediction_id,
            'verify_timestamp': datetime.now().isoformat(),
            'stock_code': target_pred.get('stock_code'),
            'stock_name': target_pred.get('stock_name'),
            'model': target_pred.get('model'),
            'pred_direction': pred_direction,
            'actual_change': actual_change,
            'direction_correct': direction_correct,
            'price_correct': price_correct,
            'support_correct': support_correct,
            'resistance_correct': resistance_correct,
            'result': result,
            'score': score
        }
        
        self._save_verification(verify_record)
        
        return {
            'success': True,
            'result': result,
            'score': score,
            'direction_correct': direction_correct,
            'price_correct': price_correct,
            'actual_close': actual_close,
            'actual_change': actual_change
        }
    
    def _save_verification(self, record: Dict):
        """保存核验记录"""
        verifications = self._load_verifications()
        verifications.append(record)
        
        with open(self.verify_file, 'w', encoding='utf-8') as f:
            json.dump(verifications, f, ensure_ascii=False, indent=2)
    
    def _load_verifications(self) -> List[Dict]:
        """加载核验记录"""
        if os.path.exists(self.verify_file):
            try:
                with open(self.verify_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def auto_verify_yesterday(self, get_actual_data_func) -> Dict:
        """自动核验昨日预测"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_preds = self.recorder.get_predictions_by_date(yesterday)
        
        results = {
            'total': len(yesterday_preds),
            'verified': 0,
            'correct': 0,
            'failed': 0,
            'details': []
        }
        
        for pred in yesterday_preds:
            if pred.get('verified'):
                continue
            
            try:
                actual_data = get_actual_data_func(pred.get('stock_code', ''))
                if actual_data:
                    verify_result = self.verify_prediction(pred.get('id'), actual_data)
                    results['verified'] += 1
                    if verify_result.get('direction_correct'):
                        results['correct'] += 1
                    else:
                        results['failed'] += 1
                    results['details'].append(verify_result)
            except Exception as e:
                print(f"核验失败 {pred.get('stock_code')}: {e}")
        
        return results


class StatisticsAnalyzer:
    """统计分析器"""
    
    def __init__(self):
        self.recorder = PredictionRecorder()
        self.verify_file = os.path.join(VERIFY_DIR, 'verification.json')
        self.stats_file = os.path.join(VERIFY_DIR, 'statistics.json')
    
    def get_overall_stats(self) -> Dict:
        """获取整体统计"""
        verifications = self._load_verifications()
        predictions = self.recorder.load_predictions()
        
        total = len(verifications)
        if total == 0:
            total = len([p for p in predictions if p.get('verified', False)])
            verifications = [p for p in predictions if p.get('verified', False)]
        
        correct = sum(1 for v in verifications if v.get('direction_correct', False))
        
        return {
            'total_predictions': len(predictions),
            'total_verified': total,
            'correct': correct,
            'failed': total - correct,
            'win_rate': round(correct / total * 100, 2) if total > 0 else 0,
            'total': total
        }
    
    def get_stats_by_model(self) -> Dict[str, Dict]:
        """按模型统计"""
        verifications = self._load_verifications()
        
        model_stats = {}
        for v in verifications:
            model = v.get('model', '')
            if not model:
                continue
            
            if model not in model_stats:
                model_stats[model] = {
                    'total': 0,
                    'correct': 0,
                    'failed': 0,
                    'win_rate': 0
                }
            
            model_stats[model]['total'] += 1
            if v.get('direction_correct'):
                model_stats[model]['correct'] += 1
            else:
                model_stats[model]['failed'] += 1
        
        for model, stats in model_stats.items():
            if stats['total'] > 0:
                stats['win_rate'] = round(stats['correct'] / stats['total'] * 100, 2)
        
        return model_stats
    
    def get_stats_by_stock(self) -> Dict[str, Dict]:
        """按股票统计"""
        verifications = self._load_verifications()
        
        stock_stats = {}
        for v in verifications:
            stock = v.get('stock_code', '')
            stock_name = v.get('stock_name', '')
            if not stock:
                continue
            
            key = f"{stock}_{stock_name}"
            if key not in stock_stats:
                stock_stats[key] = {
                    'code': stock,
                    'name': stock_name,
                    'total': 0,
                    'correct': 0,
                    'win_rate': 0
                }
            
            stock_stats[key]['total'] += 1
            if v.get('direction_correct'):
                stock_stats[key]['correct'] += 1
        
        for stock, stats in stock_stats.items():
            if stats['total'] > 0:
                stats['win_rate'] = round(stats['correct'] / stats['total'] * 100, 2)
        
        return stock_stats
    
    def get_recent_trend(self, days: int = 30) -> List[Dict]:
        """获取近期趋势"""
        verifications = self._load_verifications()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [v for v in verifications if v.get('verify_timestamp', '') > cutoff_date]
        
        trend_data = []
        for v in recent:
            trend_data.append({
                'date': v.get('verify_timestamp', '')[:10],
                'correct': 1 if v.get('direction_correct') else 0
            })
        
        return trend_data
    
    def get_win_rate_by_direction(self) -> Dict:
        """按预测方向统计胜率"""
        verifications = self._load_verifications()
        
        direction_stats = {
            '看涨': {'total': 0, 'correct': 0},
            '看跌': {'total': 0, 'correct': 0},
            '区间震荡': {'total': 0, 'correct': 0}
        }
        
        for v in verifications:
            direction = v.get('pred_direction', '')
            if direction in direction_stats:
                direction_stats[direction]['total'] += 1
                if v.get('direction_correct'):
                    direction_stats[direction]['correct'] += 1
        
        for direction, stats in direction_stats.items():
            if stats['total'] > 0:
                stats['win_rate'] = round(stats['correct'] / stats['total'] * 100, 2)
            else:
                stats['win_rate'] = 0
        
        return direction_stats
    
    def _load_verifications(self) -> List[Dict]:
        """加载核验记录"""
        if os.path.exists(self.verify_file):
            try:
                with open(self.verify_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def export_data(self, export_type: str = 'csv') -> Optional[str]:
        """导出数据"""
        if export_type == 'csv':
            verifications = self._load_verifications()
            if not verifications:
                return None
            
            df = pd.DataFrame(verifications)
            export_file = os.path.join(VERIFY_DIR, f'verification_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            df.to_csv(export_file, index=False, encoding='utf-8-sig')
            return export_file
        elif export_type == 'json':
            verifications = self._load_verifications()
            if not verifications:
                return None
            
            export_file = os.path.join(VERIFY_DIR, f'verification_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(verifications, f, ensure_ascii=False, indent=2)
            return export_file
        
        return None
    
    def clear_history(self) -> bool:
        """清空历史记录"""
        try:
            if os.path.exists(self.verify_file):
                os.remove(self.verify_file)
            if os.path.exists(self.recorder.predict_file):
                os.remove(self.recorder.predict_file)
            return True
        except Exception as e:
            print(f"清空历史失败: {e}")
            return False


# 全局实例
prediction_recorder = PredictionRecorder()
prediction_verifier = PredictionVerifier()
statistics_analyzer = StatisticsAnalyzer()
