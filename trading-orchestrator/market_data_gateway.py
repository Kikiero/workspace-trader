"""
Unified market data gateway for A-share / HK / US and news sentiment.

This module keeps data fetching deterministic and provider-specific.
It does NOT place orders and should be called before agent analysis.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class DataProviderError(RuntimeError):
    pass


@dataclass
class DataGatewayConfig:
    tushare_token: Optional[str] = None
    alpha_vantage_key: Optional[str] = None
    newsapi_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "DataGatewayConfig":
        return cls(
            tushare_token=os.getenv("TUSHARE_TOKEN"),
            alpha_vantage_key=os.getenv("ALPHAVANTAGE_API_KEY"),
            newsapi_key=os.getenv("NEWSAPI_KEY"),
        )


class MarketDataGateway:
    def __init__(self, config: Optional[DataGatewayConfig] = None, timeout_sec: int = 12):
        self.config = config or DataGatewayConfig.from_env()
        self.timeout_sec = timeout_sec

    def _get_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        merged_headers = {
            # Some providers throttle anonymous/default clients aggressively.
            "User-Agent": "workspace-trader/market-data-gateway",
            "Accept": "application/json,text/plain,*/*",
        }
        if headers:
            merged_headers.update(headers)

        last_err: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(url, headers=merged_headers)
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                    payload = resp.read().decode("utf-8")
                    return json.loads(payload)
            except HTTPError as e:
                last_err = e
                # 429/5xx → transient; retry with backoff.
                if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise DataProviderError(f"HTTP {e.code} from provider: {url}") from e
            except URLError as e:
                last_err = e
                if attempt < 4:
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise DataProviderError(f"Network error from provider: {url}") from e
            except json.JSONDecodeError as e:
                raise DataProviderError(f"Invalid JSON from provider: {url}") from e

        raise DataProviderError(f"Provider request failed after retries: {url}") from last_err

    def _post_json(self, url: str, body: Dict[str, Any]) -> Any:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload)

    def get_us_quote_yahoo(self, symbol: str) -> Dict[str, Any]:
        """
        Free quote endpoint for US/HK symbols using Yahoo Finance.
        Examples: AAPL, TSLA, 0700.HK
        """
        # Yahoo's quote endpoint is frequently rate-limited or blocked (401/429).
        # We try the quote endpoint first, then fall back to the chart endpoint.
        q = urllib.parse.quote(symbol)
        quote_url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={q}"
        try:
            data = self._get_json(quote_url)
            results = data.get("quoteResponse", {}).get("result", [])
            if results:
                row = results[0]
                return {
                    "provider": "yahoo",
                    "endpoint": "v7/quote",
                    "symbol": row.get("symbol"),
                    "price": row.get("regularMarketPrice"),
                    "change": row.get("regularMarketChange"),
                    "change_percent": row.get("regularMarketChangePercent"),
                    "currency": row.get("currency"),
                    "market_time": row.get("regularMarketTime"),
                }
        except DataProviderError:
            pass

        chart_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{q}?interval=1d&range=5d"
        data = self._get_json(chart_url)
        chart = (data.get("chart") or {})
        result = (chart.get("result") or [])
        if not result:
            raise DataProviderError(f"Yahoo chart not found: {symbol}")
        meta = (result[0].get("meta") or {})
        currency = meta.get("currency")
        market_time = meta.get("regularMarketTime")
        price = meta.get("regularMarketPrice")
        symbol_out = meta.get("symbol") or symbol
        return {
            "provider": "yahoo",
            "endpoint": "v8/chart",
            "symbol": symbol_out,
            "price": price,
            "currency": currency,
            "market_time": market_time,
        }

    def get_us_quote_alpha_vantage(self, symbol: str) -> Dict[str, Any]:
        """
        Premium/limited free quote endpoint for US symbols.
        Requires ALPHAVANTAGE_API_KEY.
        """
        key = self.config.alpha_vantage_key
        if not key:
            raise DataProviderError("Missing ALPHAVANTAGE_API_KEY")
        qs = urllib.parse.urlencode(
            {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": key,
            }
        )
        url = f"https://www.alphavantage.co/query?{qs}"
        data = self._get_json(url)
        quote = data.get("Global Quote", {})
        if not quote:
            raise DataProviderError(f"Alpha Vantage quote not found: {symbol}")
        return {
            "provider": "alpha_vantage",
            "symbol": quote.get("01. symbol"),
            "price": _to_float(quote.get("05. price")),
            "change": _to_float(quote.get("09. change")),
            "change_percent": quote.get("10. change percent"),
            "volume": _to_float(quote.get("06. volume")),
            "latest_trading_day": quote.get("07. latest trading day"),
        }

    def get_cn_daily_tushare(self, ts_code: str, trade_date: Optional[str] = None) -> Dict[str, Any]:
        """
        A-share daily bars from TuShare.
        ts_code examples: 600519.SH, 000001.SZ
        trade_date format: YYYYMMDD (optional)
        """
        token = self.config.tushare_token
        if not token:
            raise DataProviderError("Missing TUSHARE_TOKEN")

        params: Dict[str, Any] = {"ts_code": ts_code}
        if trade_date:
            params["trade_date"] = trade_date

        payload = {
            "api_name": "daily",
            "token": token,
            "params": params,
            "fields": "ts_code,trade_date,open,high,low,close,vol,amount",
        }
        data = self._post_json("http://api.tushare.pro", payload)
        result = data.get("data") or {}
        items = result.get("items") or []
        if not items:
            raise DataProviderError(f"TuShare daily not found: {ts_code}")
        first = items[0]
        return {
            "provider": "tushare",
            "ts_code": first[0],
            "trade_date": first[1],
            "open": first[2],
            "high": first[3],
            "low": first[4],
            "close": first[5],
            "vol": first[6],
            "amount": first[7],
        }

    def get_news_headlines(self, query: str, language: str = "en", page_size: int = 10) -> List[Dict[str, Any]]:
        """
        News headlines for sentiment analyst.
        Requires NEWSAPI_KEY.
        """
        key = self.config.newsapi_key
        if not key:
            raise DataProviderError("Missing NEWSAPI_KEY")

        qs = urllib.parse.urlencode(
            {
                "q": query,
                "language": language,
                "pageSize": min(page_size, 100),
                "sortBy": "publishedAt",
                "apiKey": key,
            }
        )
        url = f"https://newsapi.org/v2/everything?{qs}"
        data = self._get_json(url)
        if data.get("status") == "error":
            raise DataProviderError(data.get("message", "NewsAPI error"))
        articles = data.get("articles") or []
        return [
            {
                "provider": "newsapi",
                "title": a.get("title"),
                "source": (a.get("source") or {}).get("name"),
                "published_at": a.get("publishedAt"),
                "url": a.get("url"),
                "description": (a.get("description") or "")[:500],
            }
            for a in articles
        ]

    def get_top_headlines_us_business(self, page_size: int = 20) -> List[Dict[str, Any]]:
        """
        US business top headlines (NewsAPI). Good when you want 'latest market news' without a query.
        Requires NEWSAPI_KEY.
        """
        key = self.config.newsapi_key
        if not key:
            raise DataProviderError("Missing NEWSAPI_KEY")
        qs = urllib.parse.urlencode(
            {
                "country": "us",
                "category": "business",
                "pageSize": min(page_size, 100),
                "apiKey": key,
            }
        )
        url = f"https://newsapi.org/v2/top-headlines?{qs}"
        data = self._get_json(url)
        if data.get("status") == "error":
            raise DataProviderError(data.get("message", "NewsAPI error"))
        articles = data.get("articles") or []
        return [
            {
                "provider": "newsapi",
                "title": a.get("title"),
                "source": (a.get("source") or {}).get("name"),
                "published_at": a.get("publishedAt"),
                "url": a.get("url"),
                "description": (a.get("description") or "")[:500],
            }
            for a in articles
        ]

    def _http_get_text(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def get_google_news_rss(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Free fallback: Google News RSS search (no API key).
        Query example: 'Tesla' or 'TSLA OR Tesla' — use OR for broader match.
        """
        q = urllib.parse.quote_plus(query)
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        xml_text = self._http_get_text(url)
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            raise DataProviderError("Invalid Google News RSS: no channel")
        out: List[Dict[str, Any]] = []
        for item in channel.findall("item"):
            if len(out) >= limit:
                break
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate") or ""
            src_el = item.find("source")
            source = (src_el.text or "").strip() if src_el is not None else "Google News"
            out.append(
                {
                    "provider": "google_news_rss",
                    "title": title.strip(),
                    "source": source,
                    "published_at": pub.strip(),
                    "url": link.strip(),
                    "description": "",
                }
            )
        return out

    def get_latest_news_for_investing(
        self,
        query: str,
        page_size: int = 15,
        language: str = "en",
    ) -> List[Dict[str, Any]]:
        """
        Prefer NewsAPI if NEWSAPI_KEY is set; otherwise Google News RSS (free).
        """
        if self.config.newsapi_key:
            try:
                return self.get_news_headlines(query, language=language, page_size=page_size)
            except DataProviderError:
                pass
        return self.get_google_news_rss(query, limit=page_size)


def _to_float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    # Optional local smoke check:
    #   TUSHARE_TOKEN=... NEWSAPI_KEY=... python3 market_data_gateway.py
    gateway = MarketDataGateway()
    print("Gateway initialized. Set env vars and call methods programmatically.")

