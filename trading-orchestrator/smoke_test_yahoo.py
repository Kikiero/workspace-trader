import sys

from market_data_gateway import DataProviderError, MarketDataGateway


def main() -> int:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    g = MarketDataGateway()
    try:
        quote = g.get_us_quote_yahoo(symbol)
        print({"ok": True, "quote": quote})
        return 0
    except DataProviderError as e:
        # Yahoo may rate-limit (HTTP 429). If Alpha Vantage is configured, fall back.
        try:
            quote = g.get_us_quote_alpha_vantage(symbol)
            print({"ok": True, "provider_fallback": "alpha_vantage", "quote": quote})
            return 0
        except Exception:
            print(
                {
                    "ok": False,
                    "provider": "yahoo",
                    "symbol": symbol,
                    "error": str(e),
                    "hint": "Yahoo 可能限流；可稍后重试，或在 ENV.example 配置 ALPHAVANTAGE_API_KEY 后再跑。",
                }
            )
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

