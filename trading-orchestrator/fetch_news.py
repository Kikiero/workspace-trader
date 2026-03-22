#!/usr/bin/env python3
"""
为 OpenClaw / 投研拉取最新新闻（辅助决策，非投资建议）。

优先级:
  1) 若设置 NEWSAPI_KEY → NewsAPI（everything 或 top-headlines）
  2) 否则 → Google News RSS（无需 Key）

用法:
  export NEWSAPI_KEY=...   # 可选，见 https://newsapi.org
  python3 fetch_news.py --query "Tesla OR TSLA" --limit 15
  python3 fetch_news.py --top-business --limit 20
  python3 fetch_news.py --query "Apple" -o news.json
"""

from __future__ import annotations

import argparse
import json
import sys

from market_data_gateway import DataProviderError, MarketDataGateway


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch latest news for investing research.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--query", "-q", help="Search query, e.g. 'Tesla OR TSLA'")
    g.add_argument(
        "--top-business",
        action="store_true",
        help="US business top headlines (requires NEWSAPI_KEY)",
    )
    p.add_argument("--limit", type=int, default=15, help="Max articles (default 15)")
    p.add_argument("--lang", default="en", help="NewsAPI language code (default en)")
    p.add_argument("-o", "--output", metavar="FILE", help="Write JSON array to file")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = p.parse_args()

    gw = MarketDataGateway()

    try:
        if args.top_business:
            items = gw.get_top_headlines_us_business(page_size=args.limit)
        else:
            items = gw.get_latest_news_for_investing(
                args.query or "",
                page_size=args.limit,
                language=args.lang,
            )
    except DataProviderError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    text = json.dumps(items, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Wrote {len(items)} articles -> {args.output}", file=sys.stderr)
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
