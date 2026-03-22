# 投研新闻分析 — 参考

## 代码入口

- `MarketDataGateway.get_news_headlines(query, ...)` — NewsAPI `everything`（需 `NEWSAPI_KEY`）。
- `MarketDataGateway.get_top_headlines_us_business(...)` — 美国 `business` 头条（需 Key）。
- `MarketDataGateway.get_google_news_rss(query, limit)` — 无 Key，Google News RSS。
- `MarketDataGateway.get_latest_news_for_investing(query, ...)` — 有 Key 先试 NewsAPI，失败或未配置则 RSS。

## 环境变量

- `NEWSAPI_KEY`：可选。注册 <https://newsapi.org/register>。
- 免费层可能对 `everything` 有域名、次数限制；失败时可依赖 RSS 或换 Key/付费档。

## OpenClaw 协作

- 情绪分析：`sentiment-analyst` 的 `TOOLS.md` 已指向 `market_data_gateway` 与 NewsAPI。
- 主控编排：`trading-orchestrator/AGENTS.md` 阶段一可附加「共享新闻快照」。

## 与交易的关系

- 新闻驱动短期波动；**不等于**基本面或估值结论。
- 任何下单前必须经过 **`risk-manager`** 硬规则与用户自身风险承受度。
