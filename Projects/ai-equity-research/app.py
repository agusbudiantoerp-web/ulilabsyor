
import streamlit as st
from engine import analyze_equity, calculate_dcf, dcf_sensitivity, build_research_summary
from reports import make_excel_report, make_pdf_report
from scenario_ui import render_scenario_analysis

st.set_page_config(page_title="AI Equity Research", page_icon="📊", layout="wide")
st.title("AI Equity Research")
st.caption("Indonesian equities first · shared engine for web and Telegram · Yahoo Finance data")
st.warning("Research support only. Not investment advice. Verify data and assumptions independently.")

with st.sidebar:
    st.header("Research settings")
    symbol = st.text_input(
        "Ticker saham",
        "ANTM",
        help="Untuk saham BEI cukup masukkan ANTM. Aplikasi menambahkan .JK."
    )
    period = st.selectbox("Periode harga", ["1y", "2y", "5y", "10y"], index=2)

    st.subheader("DCF assumptions")
    years = st.slider("Forecast years", 3, 10, 5)
    growth_pct = st.number_input("Annual FCF growth (%)", -50.0, 100.0, 5.0, 1.0)
    wacc_pct = st.number_input("WACC (%)", 1.0, 100.0, 12.0, 0.5)
    terminal_pct = st.number_input("Terminal growth (%)", -10.0, 20.0, 2.5, 0.5)

    st.subheader("Currency conversion")
    fx_rate = st.number_input(
        "Reference USD/IDR rate",
        min_value=1.0,
        max_value=100000.0,
        value=18094.0,
        step=10.0,
        help="Digunakan hanya jika mata uang laporan berbeda dari mata uang saham."
    )
    fx_source_date = st.text_input("FX reference date", "2026-11-06")
    st.caption("Masukkan kurs referensi dan tanggalnya secara manual. Perbarui sebelum analisis berikutnya.")

    run = st.button("Analyze stock", type="primary", use_container_width=True)

if run:
    try:
        with st.spinner("Mengambil data pasar dan menghitung indikator..."):
            result = analyze_equity(symbol, period)
            dcf = calculate_dcf(
                result,
                years=years,
                growth=growth_pct / 100,
                wacc=wacc_pct / 100,
                terminal_growth=terminal_pct / 100,
                fx_rate=fx_rate,
                fx_source_date=fx_source_date
            )

        st.session_state["equity_result"] = result
        st.session_state["equity_dcf"] = dcf

    except Exception as exc:
        st.error(str(exc))

data = st.session_state.get("equity_result")
dcf = st.session_state.get("equity_dcf")

if data:
    st.subheader(f"{data['company']} · {data['ticker']}")

    c = st.columns(4)
    c[0].metric("Latest price", f"{data['price']:,.2f} {data['currency']}")
    c[1].metric(
        "Daily change",
        f"{data['change_pct']:.2f}%" if data.get("change_pct") is not None else "N/A"
    )
    c[2].metric(
        "Period return",
        f"{data['period_return_pct']:.2f}%" if data.get("period_return_pct") is not None else "N/A"
    )
    c[3].metric(
        "Annualized volatility",
        f"{data['annualized_volatility_pct']:.2f}%"
        if data.get("annualized_volatility_pct") is not None else "N/A"
    )

    st.caption(
        f"Harga terakhir: {data.get('latest_price_date', 'N/A')} · "
        f"Laporan laba rugi: {data.get('latest_financial_period', 'N/A')} · "
        f"Neraca: {data.get('latest_balance_period', 'N/A')} · "
        f"Arus kas: {data.get('latest_cashflow_period', 'N/A')}"
    )

    for warning in data.get("data_quality_warnings", []):
        st.warning(warning)

    st.info(data["data_quality_note"])

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Overview", "Fundamentals", "Technical", "Valuation"]
    )

    with tab1:
        st.write(f"**Sector:** {data['sector']} · **Industry:** {data['industry']}")
        st.write(f"**Data source:** {data['data_source']} · **Generated:** {data['as_of']}")

        for item in build_research_summary(data):
            st.write("• " + item)

        st.line_chart(data["history"].set_index("Date")["Close"])

    with tab2:
        st.dataframe(
            [
                {"Metric": k, "Value": v if v is not None else "N/A"}
                for k, v in data["ratios"].items()
            ],
            use_container_width=True,
            hide_index=True
        )

    with tab3:
        metrics = {
            "SMA 20": data["sma20"],
            "SMA 50": data["sma50"],
            "SMA 200": data["sma200"],
            "RSI 14": data["rsi14"]
        }

        st.dataframe(
            [
                {"Indicator": k, "Value": v if v is not None else "N/A"}
                for k, v in metrics.items()
            ],
            use_container_width=True,
            hide_index=True
        )
        st.write("Trend:", data["trend"], "· RSI:", data["rsi_signal"])

    with tab4:
        if dcf and dcf.get("available"):
            st.subheader("DCF valuation")

            st.metric(
                "Enterprise Value",
                f"{dcf['enterprise_value']:,.2f} {dcf['currency']}"
            )
            st.metric(
                "Equity Value",
                f"{dcf['equity_value']:,.2f} {dcf['currency']}"
            )
            st.metric(
                "Intrinsic Value per Share",
                f"{dcf['intrinsic_value_per_share']:,.2f} {dcf['display_currency']}"
            )

            if dcf.get("fx_conversion_applied"):
                st.caption(
                    f"Per-share conversion: {dcf['currency']} to "
                    f"{dcf['display_currency']} · "
                    f"Rate: {dcf['fx_rate']:,.2f} · "
                    f"Reference date: {dcf.get('fx_source_date') or 'Not specified'}"
                )
            else:
                st.caption(
                    f"Valuation currency: {dcf['currency']}. "
                    "No currency conversion applied."
                )

            if dcf["display_currency"] == data["currency"]:
                upside = (
                    dcf["intrinsic_value_per_share"] / data["price"] - 1
                ) * 100 if data["price"] else None

                if upside is not None:
                    st.metric("Implied upside / downside", f"{upside:+.2f}%")

            st.subheader("FCF forecast")
            st.dataframe(dcf["forecast"], use_container_width=True, hide_index=True)
            st.caption(dcf["warning"])

            sensitivity = dcf_sensitivity(
                data,
                years=years,
                terminal_growth=terminal_pct / 100,
                fx_rate=fx_rate
            )

            if sensitivity.get("available"):
                st.subheader("Sensitivity · intrinsic value per share")
                st.caption(sensitivity["warning"])
                st.dataframe(
                    sensitivity["matrix"],
                    use_container_width=True,
                    hide_index=True
                )

                with st.expander("Show enterprise value sensitivity"):
                    st.dataframe(
                        sensitivity["enterprise_value_matrix"],
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info(sensitivity.get("reason", "Sensitivity not available."))

        else:
            reason = dcf.get("reason", "Run analysis first.") if dcf else "Run analysis first."
            st.info(reason)

            if "bank" in reason.lower() or "asuransi" in reason.lower():
                st.write(
                    "Untuk bank, evaluasi P/B, ROE, pertumbuhan laba, kualitas aset, "
                    "NPL, CAR, dan pendekatan residual income atau dividend discount."
                )

        st.divider()
        render_scenario_analysis(data, fx_rate=fx_rate, years=years)

    col1, col2 = st.columns(2)

    col1.download_button(
        "Download Excel report",
        make_excel_report(data, dcf),
        file_name=f"{data['ticker'].replace('.', '_')}_research.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    col2.download_button(
        "Download PDF report",
        make_pdf_report(data, dcf),
        file_name=f"{data['ticker'].replace('.', '_')}_research.pdf",
        mime="application/pdf",
        use_container_width=True
    )

else:
    st.info("Masukkan ticker saham, atur asumsi, lalu klik Analyze stock.")
