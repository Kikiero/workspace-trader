---
name: investment-news-research
description: Fetches and structures investment-research news for OpenClaw trading workspaces using fetch_news.py and MarketDataGateway. Use when the user asks for 投研新闻、新闻分析、舆情、最新财经新闻、NewsAPI、或 workspace-trader 中的新闻拉取与解读辅助决策（非投资建议）。
---

# 投研新闻分析（Investment News Research）

## 何时使用

- 用户要做**投研/交易前信息收集**，需要**最新新闻标题与时间线**。
- 用户提到 **OpenClaw、`workspace-trader`、NewsAPI、Google News、fetch_news、情绪/舆情**。

## 硬约束

- 新闻与解读**仅供研究**，**不构成投资建议**；最终交易须符合项目内 **风控硬规则**（如 `risk-manager/risk_controls.py`）。
- 不编造未出现在拉取结果中的来源；若无法联网拉取，明确说明并建议用户本地运行脚本。

## 工作区内的实现（优先使用）

项目根（`workspace-trader`）下主控目录：

| 用途 | 路径 |
|------|------|
| 命令行拉新闻 | `trading-orchestrator/fetch_news.py` |
| 程序化 API | `trading-orchestrator/market_data_gateway.py` → `MarketDataGateway` |
| 环境变量模板 | `trading-orchestrator/ENV.example` |

**数据源策略**（与代码一致）：

- 已设置 `NEWSAPI_KEY`：优先 NewsAPI（`everything` / `top-headlines` US business）。
- 未设置 Key：使用 **Google News RSS**（`get_google_news_rss` / `get_latest_news_for_investing`）。

## 推荐执行步骤

1. **澄清标的**：股票代码与公司名（如 `TSLA` + `Tesla`），或宏观主题（如 `Fed rate`）。
2. **拉取新闻**（在仓库内执行）：

```bash
cd trading-orchestrator
# 无 Key：RSS
python3 fetch_news.py --query "Tesla OR TSLA" --limit 15 --pretty
# 有 Key：见 ENV.example 中 NEWSAPI_KEY
python3 fetch_news.py --top-business --limit 20
```

3. **结构化输出**（按下面模板汇总，不要只堆链接）。
4. **交给角色**：标题级摘要 → `sentiment-analyst`；事实与财报 → `fundamental-analyst`；主控 `trading-orchestrator` 汇总。

## 输出模板（复制使用）

```markdown
## 新闻快照
- 标的/主题：
- 时间范围：（拉取结果中的最早/最晚发布时间）
- 来源概览：（媒体类型：路透/财经媒体/自媒体等）

## 叙事主线（3 条以内）
1. ...
2. ...

## 风险与对立叙事
- ...

## 对决策的含义（非投资建议）
- 情绪/波动：
- 需验证的基本面问题：
- 建议下一步：（补数据 / 等公告 / 仅观察）

## 数据与合规
- 拉取方式：（fetch_news / NewsAPI / RSS）
- 免责声明：不构成投资建议。
```

## 更多说明

- 详细数据源与限制见 [reference.md](reference.md)。
