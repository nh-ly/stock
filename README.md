# A股智能行情分析多模型预测系统

一个功能完整的A股行情分析与智能预测系统，使用Streamlit构建Web界面。

## 功能特性

- 📊 **实时行情** - 查看A股实时行情数据
- 📈 **技术分析** - K线图、MACD、RSI、KDJ、布林带等指标
- 💰 **资金流向** - 主力资金流入流出分析
- 📰 **消息面** - 最新新闻资讯
- 🔮 **智能预测** - 四种预测模型：
  - 传统量价技术研判
  - LightGBM梯度提升树
  - XGBoost极端梯度提升
  - LSTM长短期记忆神经网络
  - 多模型集成投票融合（推荐）
- 📋 **预测记录** - 保存和管理预测历史
- 📈 **预测核验** - 验证预测准确性
- ⭐ **自选股** - 自选股管理
- 📊 **统计分析** - 模型胜率统计

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

### 部署到 Streamlit Cloud

1. Fork 或 Clone 此仓库
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 用 GitHub 账号登录
4. 点击 **New app**
5. 选择你的仓库、分支和 `app.py`
6. 点击 **Deploy**

## 依赖说明

- `streamlit` - Web 框架
- `pandas` - 数据处理
- `numpy` - 数值计算
- `akshare` - 金融数据接口
- `plotly` - 数据可视化
- `lightgbm` - 机器学习模型
- `xgboost` - 机器学习模型
- `tensorflow` - 深度学习框架

## 免责声明

本系统仅供学习研究使用，所有预测结果仅供参考，不构成任何投资建议！股市有风险，投资需谨慎。
