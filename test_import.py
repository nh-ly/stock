#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试所有模块是否正常导入"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("测试导入模块...")
print("=" * 50)

try:
    import streamlit as st
    print("✅ streamlit 导入成功")
except Exception as e:
    print(f"❌ streamlit 导入失败: {e}")

try:
    import pandas as pd
    print("✅ pandas 导入成功")
except Exception as e:
    print(f"❌ pandas 导入失败: {e}")

try:
    import numpy as np
    print("✅ numpy 导入成功")
except Exception as e:
    print(f"❌ numpy 导入失败: {e}")

try:
    import akshare as ak
    print("✅ akshare 导入成功")
except Exception as e:
    print(f"❌ akshare 导入失败: {e}")

try:
    import plotly
    print("✅ plotly 导入成功")
except Exception as e:
    print(f"❌ plotly 导入失败: {e}")

print("\n" + "=" * 50)
print("测试应用模块导入...")
print("=" * 50)

try:
    from data_fetcher import data_fetcher, DataFetcher
    print("✅ data_fetcher 导入成功")
except Exception as e:
    print(f"❌ data_fetcher 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from prediction_models import PredictionEngine, TechnicalIndicators
    print("✅ prediction_models 导入成功")
except Exception as e:
    print(f"❌ prediction_models 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from verification import prediction_recorder, prediction_verifier, statistics_analyzer
    print("✅ verification 导入成功")
except Exception as e:
    print(f"❌ verification 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from components import charts, indicators, info_components, search_components
    print("✅ components 导入成功")
except Exception as e:
    print(f"❌ components 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("测试完成！")
print("=" * 50)
