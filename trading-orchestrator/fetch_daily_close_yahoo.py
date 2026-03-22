#!/usr/bin/env python3
"""
免费拉取美股近 2 年每日收盘价（无需 API Key）。

数据源（按优先级）:
  1) Yahoo Finance v8 chart（可能被限流 429/403）
  2) Stooq 日线 CSV（美股代码形如 tsla.us，通常更稳定）

用法:
  python3 fetch_daily_close_yahoo.py TSLA
  python3 fetch_daily_close_yahoo.py AAPL -o aapl_close.csv
  python3 fetch_daily_close_yahoo.py MSFT --source stooq

依赖: 仅 Python 标准库
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple
from urllib.error import HTTPError, URLError


def _http_get(url: str, timeout: int = 30) -> bytes:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://finance.yahoo.com/",
    }
    last_err: Optional[Exception] = None
    for attempt in range(1, 6):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except HTTPError as e:
            last_err = e
            if e.code in (401, 403, 429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(min(60, 2 ** attempt))
                continue
            raise RuntimeError(f"HTTP {e.code}: {url}") from e
        except URLError as e:
            last_err = e
            if attempt < 5:
                time.sleep(2 ** (attempt - 1))
                continue
            raise RuntimeError(f"Network error: {url}") from e
    raise RuntimeError(f"Request failed: {url}") from last_err


def _get_json(url: str) -> Any:
    raw = _http_get(url)
    return json.loads(raw.decode("utf-8"))


def fetch_yahoo_daily_close_2y(symbol: str) -> Tuple[str, List[Tuple[str, Optional[float]]]]:
    sym = symbol.strip().upper()
    q = urllib.parse.quote(sym, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{q}?interval=1d&range=2y"
    data = _get_json(url)
    chart = data.get("chart") or {}
    err = chart.get("error")
    if err:
        raise RuntimeError(f"Yahoo error: {err}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"No Yahoo data: {symbol}")

    block = results[0]
    meta = block.get("meta") or {}
    symbol_out = meta.get("symbol") or sym
    timestamps: List[int] = block.get("timestamp") or []
    indicators = block.get("indicators") or {}
    quotes = (indicators.get("quote") or [{}])[0]
    closes: List[Optional[float]] = quotes.get("close") or []

    n = min(len(timestamps), len(closes))
    timestamps = timestamps[:n]
    closes = closes[:n]

    rows: List[Tuple[str, Optional[float]]] = []
    for ts, c in zip(timestamps, closes):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        rows.append((dt.isoformat(), c))

    return symbol_out, rows


def fetch_stooq_daily_close_2y(symbol: str) -> Tuple[str, List[Tuple[str, float]]]:
    """
    Stooq 美股: symbol.us，返回全历史日线 CSV；本函数只保留「最近约 2 年」交易日。
    """
    sym = symbol.strip().upper()
    stooq_ticker = f"{sym.lower()}.us"
    url = f"https://stooq.com/q/d/l/?s={urllib.parse.quote(stooq_ticker)}&i=d"
    raw = _http_get(url)
    text = raw.decode("utf-8", errors="replace")
    if not text.strip() or "No data" in text:
        raise RuntimeError(f"Stooq: no data for {stooq_ticker}")

    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if not header:
        raise RuntimeError("Stooq: empty CSV")

    # 常见表头: Date,Open,High,Low,Close,Volume
    h = [c.strip().lower() for c in header]
    try:
        di = h.index("date")
        ci = h.index("close")
    except ValueError:
        raise RuntimeError(f"Stooq: unexpected header {header}")

    cutoff = date.today() - timedelta(days=730)
    rows: List[Tuple[str, float]] = []
    for parts in reader:
        if len(parts) <= max(di, ci):
            continue
        d_str = parts[di].strip()
        try:
            d = date.fromisoformat(d_str)
        except ValueError:
            continue
        if d < cutoff:
            continue
        try:
            close = float(parts[ci].replace(",", ""))
        except ValueError:
            continue
        rows.append((d.isoformat(), close))

    rows.sort(key=lambda x: x[0])
    return sym, rows


def fetch_daily_close_2y_auto(symbol: str) -> Tuple[str, str, List[Tuple[str, Optional[float]]]]:
    """返回 (数据源名, 展示用代码, 行列表)。"""
    try:
        s, rows = fetch_yahoo_daily_close_2y(symbol)
        return ("yahoo", s, rows)
    except Exception as y_err:
        try:
            s, rows = fetch_stooq_daily_close_2y(symbol)
            flat: List[Tuple[str, Optional[float]]] = [(d, c) for d, c in rows]
            return ("stooq", s, flat)
        except Exception as s_err:
            raise RuntimeError(
                f"Yahoo 失败: {y_err}; Stooq 失败: {s_err}"
            ) from s_err


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch ~2 years of US stock daily close (free).")
    p.add_argument("symbol", help="US ticker e.g. TSLA, AAPL")
    p.add_argument("-o", "--output", metavar="FILE", help="Write CSV; default stdout")
    p.add_argument("--skip-missing", action="store_true", help="Skip null closes (Yahoo only)")
    p.add_argument(
        "--source",
        choices=("auto", "yahoo", "stooq"),
        default="auto",
        help="Data source (default: try Yahoo then Stooq)",
    )
    args = p.parse_args()

    try:
        if args.source == "yahoo":
            sym, rows = fetch_yahoo_daily_close_2y(args.symbol)
            src = "yahoo"
        elif args.source == "stooq":
            sym, rows_s = fetch_stooq_daily_close_2y(args.symbol)
            rows = [(d, c) for d, c in rows_s]
            src = "stooq"
        else:
            src, sym, rows = fetch_daily_close_2y_auto(args.symbol)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.skip_missing:
        rows = [(d, c) for d, c in rows if c is not None]

    lines = ["date,close", *[f"{d},{'' if c is None else c}" for d, c in rows]]
    text = "\n".join(lines) + "\n"
    meta = f"# source={src} symbol={sym} rows={len(rows)}\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(meta)
            f.write(text)
        print(meta.strip(), file=sys.stderr)
        print(f"Wrote {len(rows)} rows -> {args.output}", file=sys.stderr)
    else:
        sys.stderr.write(meta)
        sys.stdout.write(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
