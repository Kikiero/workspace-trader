# TOOLS.md - Local Notes

## 工具策略（主控只“调度”，不“亲自下场”）

## 允许使用

- **调用其他 Agent**：分派任务、收集结论、要求补充与校验
- **结构化汇总**：将多方输出合并成最终建议与执行计划
- **数据接入骨架（只读）**：`market_data_gateway.py`（用于在分派前准备共享数据，不做最终分析）
- **新闻拉取（只读）**：`fetch_news.py` 或 `MarketDataGateway.get_latest_news_for_investing()`（NewsAPI 优先，无 Key 时 Google News RSS）

## 禁止/不应使用

- **直接数据抓取/研究工具**：由分析角色使用
- **直接交易 API**：由交易员执行，且必须经过风控

