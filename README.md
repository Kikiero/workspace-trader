# workspace-trader

OpenClaw 交易团队工作区：多 Agent 角色、主控编排、硬风控、行情与新闻拉取（示例脚本）。

## 密钥配置

**不要**把 API Key 提交到仓库。复制 `trading-orchestrator/ENV.example` 为本地 `.env` 或 `ENV`（已在 `.gitignore` 中忽略），并填写密钥。详见 [SECURITY.md](SECURITY.md)。

## 目录说明

- `trading-orchestrator/` — 主控、`market_data_gateway.py`、`fetch_news.py`、`fetch_daily_close_yahoo.py`
- `risk-manager/` — `risk_controls.py` 硬编码风控与单元测试
- `*-trader/`、`fundamental-analyst/` 等 — 各 Agent 的 `IDENTITY.md` / `SOUL.md` / `AGENTS.md`
- `.cursor/skills/investment-news-research/` — Cursor Skill「投研新闻分析」

## 推送到 GitHub

在 GitHub 新建空仓库后：

```bash
cd /path/to/workspace-trader
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git branch -M main
git push -u origin main
```

若使用 SSH：`git remote add origin git@github.com:<username>/<repo>.git`
