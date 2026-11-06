
"""Market and ticker normalization for AI Equity Research V2."""

import re


def resolve_market_ticker(symbol: str, market: str) -> dict:
    """
    Normalize a ticker for the selected market.

    IDX: BBCA -> BBCA.JK, currency IDR
    US:  AAPL -> AAPL, currency USD

    Market selection is explicit to avoid ambiguous ticker detection.
    """
    raw = (symbol or "").strip().upper().replace(" ", "")
    selected_market = (market or "").strip().upper()

    if not raw:
        raise ValueError("Masukkan kode saham.")

    if selected_market in {"INDONESIA", "IDX", "BEI"}:
        selected_market = "IDX"

        if raw.endswith(".JK"):
            code = raw[:-3]
        elif "." in raw or "-" in raw:
            raise ValueError(
                "Format ticker IDX tidak valid. "
                "Gunakan contoh BBCA atau BBCA.JK."
            )
        else:
            code = raw

        if not re.fullmatch(r"[A-Z0-9]{3,6}", code):
            raise ValueError("Kode saham IDX tidak valid.")

        return {
            "market": "IDX",
            "exchange": "Indonesia Stock Exchange",
            "ticker": f"{code}.JK",
            "currency": "IDR",
        }

    if selected_market in {"US", "USA", "UNITED STATES"}:
        selected_market = "US"

        if raw.endswith(".JK"):
            raise ValueError(
                "Ticker .JK adalah saham Indonesia, bukan saham US."
            )

        # Yahoo Finance uses BRK-B rather than BRK.B.
        code = raw.replace(".", "-")

        if not re.fullmatch(r"[A-Z][A-Z0-9]{0,4}(?:-[A-Z0-9]{1,2})?", code):
            raise ValueError(
                "Format ticker US tidak valid. "
                "Contoh: AAPL, NVDA, MSFT, atau BRK-B."
            )

        return {
            "market": "US",
            "exchange": "United States",
            "ticker": code,
            "currency": "USD",
        }

    raise ValueError("Pilih market IDX atau US.")
