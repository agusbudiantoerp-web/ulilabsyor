import yfinance as yf

tickers = ["TPIA.JK", "ANTM.JK", "BBCA.JK", "PTBA.JK"]

for symbol in tickers:
    print("\n" + "=" * 65)
    print("TICKER:", symbol)

    t = yf.Ticker(symbol)
    info = t.info

    print("Currency:", info.get("currency"))
    print("Financial currency:", info.get("financialCurrency"))
    print("Trailing PE:", info.get("trailingPE"))
    print("Price to book:", info.get("priceToBook"))
    print("ROE:", info.get("returnOnEquity"))
    print("Debt to equity:", info.get("debtToEquity"))
    print("Dividend yield:", info.get("dividendYield"))
    print("Dividend rate:", info.get("dividendRate"))

    for name in ["financials", "balance_sheet", "cashflow"]:
        frame = getattr(t, name)
        print("\n", name.upper())

        if frame.empty:
            print("DATA TIDAK TERSEDIA")
            continue

        print("Period:", list(frame.columns[:2]))

        for label in frame.index:
            text = str(label).lower()
            if any(word in text for word in [
                "operating", "cash flow", "cashflow",
                "net income", "ebitda", "capital expenditure",
                "revenue", "total debt", "cash and cash"
            ]):
                print(label, "=", frame.loc[label].iloc[:2].to_dict())
