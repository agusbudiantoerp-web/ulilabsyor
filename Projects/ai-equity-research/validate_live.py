
"""Manual live-data validation for selected IDX issuers.

Run from this directory:
    python validate_live.py

This is a data availability and consistency check,
not a financial-statement audit or investment recommendation.
"""

import json
from engine import analyze_equity, calculate_dcf

TICKERS = ["TPIA", "ANTM", "BBCA", "PTBA"]

for symbol in TICKERS:
    print("\n" + "=" * 75)
    print("LIVE DATA VALIDATION:", symbol)

    try:
        data = analyze_equity(symbol, period="2y")
        dcf = calculate_dcf(data)
        ratios = data.get("ratios", {})

        result = {
            "ticker": data.get("ticker"),
            "company": data.get("company"),
            "sector": data.get("sector"),
            "industry": data.get("industry"),

            "quote_currency": data.get("quote_currency"),
            "financial_currency": data.get("financial_currency"),
            "currency": data.get("currency"),

            "latest_price_date": data.get("latest_price_date"),
            "latest_price": data.get("price"),

            "financial_periods": {
                "income_statement": data.get("latest_financial_period"),
                "balance_sheet": data.get("latest_balance_period"),
                "cash_flow": data.get("latest_cashflow_period"),
            },

            "financial_data": {
                "revenue": ratios.get("Revenue"),
                "net_income_parent": ratios.get(
                    "Net income attributable to parent"
                ),
                "net_income_including_nci": ratios.get(
                    "Net income including noncontrolling interests"
                ),
                "net_income": ratios.get("Net income"),
                "operating_cash_flow": ratios.get("Operating cash flow"),
                "capital_expenditure": ratios.get("Capital expenditure"),
                "free_cash_flow": ratios.get("Free cash flow"),
                "EBITDA": ratios.get("EBITDA"),
            },

            "valuation_and_ratios": {
                "PE": ratios.get("Trailing P/E"),
                "PB": ratios.get("Price to book"),
                "ROE": ratios.get("ROE (%)"),
                "debt_to_equity": ratios.get("Debt to equity"),
                "dividend_yield": ratios.get("Dividend yield (%)"),
            },

            "dcf": {
                "available": dcf.get("available"),
                "reason": dcf.get("reason"),
                "currency": dcf.get("currency"),
            },

            "data_quality_warnings": data.get(
                "data_quality_warnings", []
            ),
            "data_source": data.get("data_source"),
        }

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as exc:
        print(json.dumps({
            "ticker": symbol,
            "error": str(exc)
        }, indent=2, ensure_ascii=False))
