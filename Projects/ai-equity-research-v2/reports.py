
"""Excel and PDF report builders for AI Equity Research."""

from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def make_excel_report(data: dict, dcf: dict | None = None) -> bytes:
    out = BytesIO()

    ratios = pd.DataFrame([
        {"Metric": key, "Value": value}
        for key, value in data["ratios"].items()
    ])

    snapshot = pd.DataFrame([{
        "Ticker": data["ticker"],
        "Company": data["company"],
        "Sector": data["sector"],
        "Industry": data["industry"],
        "Quote currency": data["currency"],
        "Financial currency": data.get("financial_currency"),
        "As of UTC": data["as_of"],
        "Latest price date": data.get("latest_price_date"),
        "Income statement period": data.get("latest_financial_period"),
        "Balance sheet period": data.get("latest_balance_period"),
        "Cash flow period": data.get("latest_cashflow_period"),
        "Latest price": data["price"],
        "Daily change %": data["change_pct"],
        "Period return %": data["period_return_pct"],
        "Trend": data["trend"],
        "RSI 14": data["rsi14"],
        "Annualized volatility %": data["annualized_volatility_pct"],
        "Data source": data["data_source"],
        "Data quality note": data.get("data_quality_note")
    }])

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        snapshot.to_excel(writer, sheet_name="Summary", index=False)
        ratios.to_excel(writer, sheet_name="Fundamentals", index=False)
        data["history"].to_excel(writer, sheet_name="Price History", index=False)

        warnings = data.get("data_quality_warnings", [])
        pd.DataFrame({
            "Data quality warnings": warnings or [
                "No automatic warning; manual source verification still required."
            ]
        }).to_excel(writer, sheet_name="Data Quality", index=False)

        if dcf and dcf.get("available"):
            dcf["forecast"].to_excel(
                writer,
                sheet_name="DCF Forecast",
                index=False
            )

            dcf_rows = [
                {"Metric": "Enterprise value", "Value": dcf["enterprise_value"]},
                {"Metric": "PV forecast", "Value": dcf["pv_forecast"]},
                {"Metric": "Terminal value", "Value": dcf["terminal_value"]},
                {"Metric": "PV terminal value", "Value": dcf["pv_terminal_value"]},
                {"Metric": "Total debt", "Value": dcf["total_debt"]},
                {"Metric": "Cash and equivalents", "Value": dcf["cash"]},
                {"Metric": "Net debt", "Value": dcf["net_debt"]},
                {"Metric": "Equity value", "Value": dcf["equity_value"]},
                {"Metric": "Shares outstanding", "Value": dcf["shares_outstanding"]},
                {
                    "Metric": "Intrinsic value per share",
                    "Value": dcf["intrinsic_value_per_share"]
                },
                {"Metric": "Financial currency", "Value": dcf["currency"]},
                {"Metric": "Display currency", "Value": dcf["display_currency"]},
                {"Metric": "FX conversion applied", "Value": dcf["fx_conversion_applied"]},
                {"Metric": "FX rate", "Value": dcf["fx_rate"]},
                {"Metric": "FX reference date", "Value": dcf["fx_source_date"]}
            ]

            dcf_rows += [
                {"Metric": key, "Value": value}
                for key, value in dcf["assumptions"].items()
            ]

            pd.DataFrame(dcf_rows).to_excel(
                writer,
                sheet_name="DCF Valuation",
                index=False
            )

            pd.DataFrame({
                "DCF notes": [dcf["warning"]]
            }).to_excel(writer, sheet_name="DCF Notes", index=False)

        else:
            reason = dcf.get("reason", "DCF not run") if dcf else "DCF not run"
            pd.DataFrame({
                "DCF status": [reason]
            }).to_excel(writer, sheet_name="DCF Valuation", index=False)

        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions

            for col in ws.columns:
                letter = col[0].column_letter
                max_len = max(
                    (len(str(cell.value)) if cell.value is not None else 0)
                    for cell in col
                )
                ws.column_dimensions[letter].width = min(
                    max(max_len + 2, 12),
                    42
                )

    return out.getvalue()


def make_pdf_report(data: dict, dcf: dict | None = None) -> bytes:
    out = BytesIO()

    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        rightMargin=38,
        leftMargin=38,
        topMargin=38,
        bottomMargin=38
    )

    styles = getSampleStyleSheet()

    company = escape(str(data["company"]))
    ticker = escape(str(data["ticker"]))

    story = [
        Paragraph("AI Equity Research Report", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"{company} ({ticker})", styles["Heading2"]),
        Paragraph(
            f"Sector: {escape(str(data['sector']))} | "
            f"Industry: {escape(str(data['industry']))} | "
            f"Quote currency: {escape(str(data['currency']))} | "
            f"Financial currency: {escape(str(data.get('financial_currency', 'N/A')))}",
            styles["Normal"]
        ),
        Paragraph(
            f"Generated (UTC): {escape(str(data['as_of']))}",
            styles["Normal"]
        ),
        Paragraph(
            f"Price date: {escape(str(data.get('latest_price_date', 'N/A')))} | "
            f"Income statement: {escape(str(data.get('latest_financial_period', 'N/A')))} | "
            f"Balance sheet: {escape(str(data.get('latest_balance_period', 'N/A')))} | "
            f"Cash flow: {escape(str(data.get('latest_cashflow_period', 'N/A')))}",
            styles["Normal"]
        ),
        Spacer(1, 14)
    ]

    rows = [
        ["Metric", "Value"],
        ["Latest price", str(data.get("price")) + " " + str(data.get("currency"))],
        ["Daily change (%)", str(data.get("change_pct"))],
        ["Period return (%)", str(data.get("period_return_pct"))],
        ["Trend", str(data.get("trend"))],
        ["RSI 14", str(data.get("rsi14"))],
        ["Annualized volatility (%)", str(data.get("annualized_volatility_pct"))]
    ]

    table = Table(rows, colWidths=[210, 250])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163447")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .4, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6)
    ]))

    story += [
        table,
        Spacer(1, 14),
        Paragraph("Fundamental data", styles["Heading2"])
    ]

    fundamental_rows = [["Metric", "Value"]] + [
        [str(key), "N/A" if value is None else str(value)]
        for key, value in data["ratios"].items()
    ]

    fundamental_table = Table(
        fundamental_rows,
        colWidths=[210, 250],
        repeatRows=1
    )

    fundamental_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163447")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .3, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 4)
    ]))

    story += [
        fundamental_table,
        Spacer(1, 14),
        Paragraph("Data quality checks", styles["Heading2"])
    ]

    warnings = data.get("data_quality_warnings", []) or [
        "No automatic warning; manual source verification is still required."
    ]

    for warning in warnings:
        story.append(
            Paragraph("• " + escape(str(warning)), styles["BodyText"])
        )

    story.append(Spacer(1, 10))

    if dcf and dcf.get("available"):
        dcf_rows = [
            ["DCF metric", "Value"],
            ["Enterprise value", f"{dcf['enterprise_value']:,.2f} {dcf['currency']}"],
            ["PV forecast", f"{dcf['pv_forecast']:,.2f} {dcf['currency']}"],
            ["PV terminal value", f"{dcf['pv_terminal_value']:,.2f} {dcf['currency']}"],
            ["Total debt", f"{dcf['total_debt']:,.2f} {dcf['currency']}"],
            ["Cash and equivalents", f"{dcf['cash']:,.2f} {dcf['currency']}"],
            ["Net debt", f"{dcf['net_debt']:,.2f} {dcf['currency']}"],
            ["Equity value", f"{dcf['equity_value']:,.2f} {dcf['currency']}"],
            ["Shares outstanding", f"{dcf['shares_outstanding']:,.0f}"],
            [
                "Intrinsic value per share",
                f"{dcf['intrinsic_value_per_share']:,.2f} {dcf['display_currency']}"
            ]
        ]

        dcf_table = Table(dcf_rows, colWidths=[210, 250], repeatRows=1)
        dcf_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163447")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 5)
        ]))

        story += [
            Paragraph("DCF Valuation", styles["Heading2"]),
            dcf_table,
            Spacer(1, 8)
        ]

        if dcf.get("fx_conversion_applied"):
            fx_note = (
                f"FX conversion: {dcf['currency']} to {dcf['display_currency']} | "
                f"Rate: {dcf['fx_rate']:,.2f} | "
                f"Reference date: {dcf.get('fx_source_date') or 'Not specified'}"
            )
            story.append(Paragraph(escape(fx_note), styles["BodyText"]))

        story += [
            Spacer(1, 6),
            Paragraph(escape(dcf["warning"]), styles["BodyText"]),
            Spacer(1, 10)
        ]

    else:
        reason = dcf.get("reason", "DCF not run") if dcf else "DCF not run"

        story += [
            Paragraph("DCF not presented", styles["Heading2"]),
            Paragraph(escape(reason), styles["BodyText"]),
            Spacer(1, 10)
        ]

    story += [
        Paragraph("Important limitations", styles["Heading2"]),
        Paragraph(escape(str(data["disclaimer"])), styles["BodyText"]),
        Paragraph(
            "This report is generated from third-party market data and automated "
            "calculations. Verify source data, accounting periods, units, corporate "
            "actions and assumptions independently. It is not a recommendation "
            "to buy or sell securities.",
            styles["BodyText"]
        )
    ]

    doc.build(story)
    return out.getvalue()
