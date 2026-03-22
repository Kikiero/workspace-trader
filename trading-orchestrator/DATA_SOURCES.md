# Data Sources (市场覆盖与接入)

这套 `workspace-trader` 的分析框架不限定市场；市场覆盖取决于“数据源是否接入”。

## 已提供的接入骨架

统一入口：`market_data_gateway.py`

- **A 股日线**：TuShare Pro（需要 `TUSHARE_TOKEN`）
- **美股/港股实时报价**：Yahoo Finance（无需 key，适合快速报价）
- **美股报价（可选）**：Alpha Vantage（需要 `ALPHAVANTAGE_API_KEY`）
- **新闻标题**：NewsAPI（需要 `NEWSAPI_KEY`）

## 配置方式

在 `ENV.example` 填入 key，然后在 shell 里导出：

```bash
export TUSHARE_TOKEN="..."
export ALPHAVANTAGE_API_KEY="..."
export NEWSAPI_KEY="..."
```

## 最短可跑通示例

```python
from market_data_gateway import MarketDataGateway

g = MarketDataGateway()
print(g.get_us_quote_yahoo("AAPL"))
print(g.get_cn_daily_tushare("600519.SH"))
print(g.get_news_headlines("Apple", language="en", page_size=5))
```

## 美股近 2 年每日收盘价（脚本）

无需 Key，见 `fetch_daily_close_yahoo.py`：

- 默认 **auto**：先试 Yahoo，失败则自动用 Stooq
- 仅 Stooq：`python3 fetch_daily_close_yahoo.py TSLA --source stooq -o tsla.csv`

输出 CSV：`date,close`

## 最新新闻（投研辅助）

入口：`market_data_gateway.py` + 命令行 `fetch_news.py`。

| 方式 | 是否需要 Key | 说明 |
|------|----------------|------|
| **NewsAPI** | 需要 `NEWSAPI_KEY` | `everything` / `top-headlines`（美國 business） |
| **Google News RSS** | 不需要 | `get_google_news_rss` / `get_latest_news_for_investing` 在无 Key 时自动回退 |

配置：把 key 写入环境变量（见 `ENV.example`），例如：

```bash
export NEWSAPI_KEY="你的key"
```

拉取示例：

```bash
python3 fetch_news.py --query "Tesla OR TSLA" --limit 15
python3 fetch_news.py --top-business --limit 20
```

**注意**：NewsAPI 免费层对 `everything` 可能有域名/次数限制；若失败会自动尝试 RSS（当使用 `get_latest_news_for_investing` 且 NewsAPI 抛错时）。命令行 `fetch_news.py` 在无 Key 时直接走 RSS。

## 角色使用建议（映射）

- `technical-analyst`：行情/K 线/成交量（`get_cn_daily_tushare` 或 quote + 未来可扩展 K 线）
- `fundamental-analyst`：财报/公告（建议后续接 TuShare 财务接口或另选财报源）
- `sentiment-analyst`：新闻标题 + 社媒（当前提供 NewsAPI，社媒需另接）

