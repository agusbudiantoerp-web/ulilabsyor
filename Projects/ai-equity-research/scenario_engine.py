
"""Scenario-based DCF engine for AI Equity Research V1.

All financial inputs use the same financial currency.
Per-share values are converted to quote currency using fx_rate.
"""

def project_scenario(financials: dict, assumptions: dict, years: int = 5) -> dict:
    required = [
        "revenue_ttm",
        "net_debt",
        "shares_outstanding",
        "current_price",
        "fx_rate",
    ]

    missing = [key for key in required if financials.get(key) is None]
    if missing:
        return {
            "available": False,
            "reason": f"Financial data missing: {', '.join(missing)}",
        }

    required_assumptions = [
        "revenue_growth",
        "ebitda_margin",
        "da_pct_revenue",
        "capex_pct_revenue",
        "nwc_pct_revenue",
        "tax_rate",
        "wacc",
        "terminal_growth",
    ]

    missing = [
        key for key in required_assumptions
        if assumptions.get(key) is None
    ]
    if missing:
        return {
            "available": False,
            "reason": f"Assumptions missing: {', '.join(missing)}",
        }

    revenue = float(financials["revenue_ttm"])
    net_debt = float(financials["net_debt"])
    shares = float(financials["shares_outstanding"])
    current_price = float(financials["current_price"])
    fx_rate = float(financials["fx_rate"])

    growth = float(assumptions["revenue_growth"])
    margin = float(assumptions["ebitda_margin"])
    da_pct = float(assumptions["da_pct_revenue"])
    capex_pct = float(assumptions["capex_pct_revenue"])
    nwc_pct = float(assumptions["nwc_pct_revenue"])
    tax_rate = float(assumptions["tax_rate"])
    wacc = float(assumptions["wacc"])
    terminal_growth = float(assumptions["terminal_growth"])

    if years < 1 or years > 20:
        return {"available": False, "reason": "Years must be 1-20."}

    if min(revenue, shares, current_price, fx_rate) <= 0:
        return {"available": False, "reason": "Invalid financial input."}

    if wacc <= terminal_growth:
        return {
            "available": False,
            "reason": "WACC must be higher than terminal growth.",
        }

    if not 0 <= tax_rate <= 1:
        return {"available": False, "reason": "Invalid tax rate."}

    forecast = []
    previous_revenue = revenue
    pv_fcff = 0.0

    for year in range(1, years + 1):
        revenue *= 1 + growth
        ebitda = revenue * margin
        depreciation = revenue * da_pct
        ebit = ebitda - depreciation
        tax = max(ebit, 0) * tax_rate
        capex = revenue * capex_pct
        change_nwc = (revenue - previous_revenue) * nwc_pct

        fcff = ebit - tax + depreciation - capex - change_nwc
        pv = fcff / ((1 + wacc) ** year)
        pv_fcff += pv

        forecast.append({
            "year": year,
            "revenue": revenue,
            "ebitda": ebitda,
            "ebit": ebit,
            "capex": capex,
            "change_nwc": change_nwc,
            "fcff": fcff,
            "present_value": pv,
        })

        previous_revenue = revenue

    terminal_fcff = forecast[-1]["fcff"]

    if terminal_fcff <= 0:
        return {
            "available": False,
            "reason": "Year 5 FCFF is not positive; terminal DCF is not reliable.",
            "forecast": forecast,
        }

    terminal_value = (
        terminal_fcff * (1 + terminal_growth)
        / (wacc - terminal_growth)
    )
    pv_terminal = terminal_value / ((1 + wacc) ** years)

    enterprise_value = pv_fcff + pv_terminal
    equity_value = enterprise_value - net_debt

    if equity_value <= 0:
    	return {
            "available": False,
            "reason": "Enterprise Value belum cukup menutup net debt. Equity Value tidak positif.",
            "forecast": forecast,
            "enterprise_value": enterprise_value,
            "net_debt": net_debt,
            "equity_value": equity_value,
        }

    intrinsic_usd = equity_value / shares
    intrinsic_quote = intrinsic_usd * fx_rate

    upside_pct = (
        (intrinsic_quote / current_price) - 1
    ) * 100

    return {
        "available": True,
        "forecast": forecast,
        "pv_fcff": pv_fcff,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "enterprise_value": enterprise_value,
        "net_debt": net_debt,
        "equity_value": equity_value,
        "intrinsic_value_financial_currency": intrinsic_usd,
        "intrinsic_value_per_share": intrinsic_quote,
        "current_price": current_price,
        "upside_downside_pct": upside_pct,
        "currency": "IDR",
        "assumptions": assumptions,
        "warning": (
            "Scenario valuation is assumption-driven, not a guaranteed "
            "share price forecast."
        ),
    }


def run_scenarios(financials: dict, scenarios: dict, years: int = 5) -> dict:
    results = {}

    for name, assumptions in scenarios.items():
        results[name] = project_scenario(
            financials=financials,
            assumptions=assumptions,
            years=years,
        )

    return {
        "ticker": financials.get("ticker", "Unknown"),
        "years": years,
        "scenarios": results,
    }


def scenario_sensitivity(
    financials: dict,
    assumptions: dict,
    wacc_values=None,
    terminal_growth_values=None,
    years: int = 5,
) -> dict:
    """Calculate DCF sensitivity across WACC and terminal growth."""

    if wacc_values is None:
        wacc_values = [0.09, 0.10, 0.11, 0.12, 0.13]

    if terminal_growth_values is None:
        terminal_growth_values = [0.02, 0.025, 0.03]

    results = []

    for wacc in wacc_values:
        row = {
            "wacc": wacc,
            "values": [],
        }

        for terminal_growth in terminal_growth_values:
            test_assumptions = assumptions.copy()
            test_assumptions["wacc"] = wacc
            test_assumptions["terminal_growth"] = terminal_growth

            result = project_scenario(
                financials,
                test_assumptions,
                years=years,
            )

            if result.get("enterprise_value") is None:
                cell = {
                    "available": False,
                    "value_per_share": None,
                    "equity_value": None,
                    "reason": result.get("reason"),
                }
            else:
                equity_value = result.get("equity_value")

                if equity_value is not None and equity_value > 0:
                    value_per_share = (
                        equity_value
                        / float(financials["shares_outstanding"])
                        * float(financials["fx_rate"])
                    )

                    cell = {
                        "available": True,
                        "value_per_share": value_per_share,
                        "equity_value": equity_value,
                        "reason": None,
                    }
                else:
                    cell = {
                        "available": False,
                        "value_per_share": None,
                        "equity_value": equity_value,
                        "reason": "Equity Value tidak positif.",
                    }

            row["values"].append(cell)

        results.append(row)

    return {
        "available": True,
        "ticker": financials.get("ticker", "Unknown"),
        "currency": financials.get("quote_currency", "IDR"),
        "terminal_growth_values": terminal_growth_values,
        "sensitivity": results,
        "note": (
            "N/M berarti valuasi per saham tidak bermakna "
            "karena Equity Value tidak positif atau DCF tidak tersedia."
        ),
    }


    results = {}

    for name, assumptions in scenarios.items():
        results[name] = project_scenario(
            financials=financials,
            assumptions=assumptions,
            years=years,
        )

    return {
        "ticker": financials.get("ticker", "Unknown"),
        "years": years,
        "scenarios": results,
    }
