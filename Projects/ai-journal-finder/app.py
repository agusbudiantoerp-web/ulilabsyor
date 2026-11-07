
import streamlit as st
import pandas as pd

from paper_engine import search_papers
from journal_engine import search_journals

st.set_page_config(
    page_title="AI Journal Finder",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Journal Finder")
st.caption(
    "Multidisciplinary scholarly paper discovery "
    "and journal search"
)

st.info(
    "Data pencarian berasal dari OpenAlex. "
    "Metadata dan status indeksasi perlu diverifikasi "
    "sebelum digunakan untuk keputusan publikasi."
)

tab_papers, tab_journals = st.tabs([
    "🔎 Paper Finder",
    "📖 Journal Finder"
])


def download_buttons(data, filename):
    if data.empty:
        return

    csv_data = data.to_csv(index=False).encode("utf-8-sig")

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv"
        )

    with col2:
        excel_data = None

        try:
            from io import BytesIO

            buffer = BytesIO()

            with pd.ExcelWriter(
                buffer,
                engine="openpyxl"
            ) as writer:
                data.to_excel(
                    writer,
                    index=False,
                    sheet_name="Results"
                )

            excel_data = buffer.getvalue()

        except Exception as exc:
            st.error(f"Excel export error: {exc}")

        if excel_data:
            st.download_button(
                "Download Excel",
                data=excel_data,
                file_name=f"{filename}.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
            )


with tab_papers:
    st.subheader("Search Scholarly Papers")

    with st.form("paper_search_form"):
        paper_query = st.text_input(
            "Research topic or keywords",
            placeholder="Example: artificial intelligence in education"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            year_from = st.number_input(
                "From year",
                min_value=1900,
                max_value=2100,
                value=2020
            )

        with col2:
            year_to = st.number_input(
                "To year",
                min_value=1900,
                max_value=2100,
                value=2026
            )

        with col3:
            paper_limit = st.selectbox(
                "Maximum results",
                [10, 20, 50, 100],
                index=1
            )

        paper_submit = st.form_submit_button(
            "Search Papers",
            type="primary"
        )

    if paper_submit:
        if not paper_query.strip():
            st.warning("Please enter a research topic.")
        elif year_from > year_to:
            st.warning("From year cannot exceed To year.")
        else:
            with st.spinner("Searching OpenAlex..."):
                try:
                    papers = search_papers(
                        query=paper_query,
                        per_page=paper_limit,
                        year_from=year_from,
                        year_to=year_to
                    )

                    if papers:
                        df = pd.DataFrame(papers)

                        st.success(
                            f"Found {len(df)} scholarly papers."
                        )

                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "paper_url": st.column_config.LinkColumn(
                                    "Paper link"
                                ),
                                "pdf_url": st.column_config.LinkColumn(
                                    "Open access PDF"
                                )
                            }
                        )

                        download_buttons(
                            df,
                            "ai_journal_finder_papers"
                        )

                    else:
                        st.warning("No papers found.")

                except Exception as exc:
                    st.error(str(exc))


with tab_journals:
    st.subheader("Search Academic Journals")

    with st.form("journal_search_form"):
        journal_query = st.text_input(
            "Journal name or research field",
            placeholder="Example: multidisciplinary research"
        )

        journal_limit = st.selectbox(
            "Maximum results",
            [10, 20, 50, 100],
            index=1,
            key="journal_limit"
        )

        journal_submit = st.form_submit_button(
            "Search Journals",
            type="primary"
        )

    if journal_submit:
        if not journal_query.strip():
            st.warning("Please enter a journal name or topic.")
        else:
            with st.spinner("Searching OpenAlex sources..."):
                try:
                    journals = search_journals(
                        query=journal_query,
                        per_page=journal_limit
                    )

                    if journals:
                        df = pd.DataFrame(journals)

                        st.success(
                            f"Found {len(df)} journals."
                        )

                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "website": st.column_config.LinkColumn(
                                    "Journal website"
                                )
                            }
                        )

                        st.warning(
                            "OpenAlex metadata is not proof of "
                            "Scopus, Web of Science, or SINTA indexing. "
                            "Verify each journal through official sources."
                        )

                        download_buttons(
                            df,
                            "ai_journal_finder_journals"
                        )

                    else:
                        st.warning("No journals found.")

                except Exception as exc:
                    st.error(str(exc))


st.divider()

st.caption(
    "AI Journal Finder V1.0 | Research discovery support. "
    "Always verify journal policies, indexing, and publication fees."
)
