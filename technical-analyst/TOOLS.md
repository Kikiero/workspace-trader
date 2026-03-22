# TOOLS.md — 技术分析师可用工具（能力白名单）

## 允许使用

- **行情数据 API**：
  - A 股：可对接 `trading-orchestrator/market_data_gateway.py` 的 TuShare（日线示例：`get_cn_daily_tushare`）
  - 港/美股：可对接 `trading-orchestrator/market_data_gateway.py` 的 Yahoo Quote（示例：`get_us_quote_yahoo`）
  - 美股（可选）：Alpha Vantage Quote（示例：`get_us_quote_alpha_vantage`）
- **指标计算**：MA/EMA、RSI、MACD、布林带、ATR 等
- **绘图/可视化**：画线、区间标注、结构截图（如环境支持）

## 禁止/不应使用

- **交易下单相关**：不调用交易 API
- **财务/情绪建模**：不替代基本面/情绪角色输出

## 输出约束

- 给出的关键位与策略必须说明：**使用的周期（1h/4h/1d/1w）与触发条件**。
