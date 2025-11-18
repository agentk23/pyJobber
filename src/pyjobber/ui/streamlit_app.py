import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from ..storage.csv_handler import csv_files_exist, load_jobs_from_csv
from ..core.background_scraper import get_background_scraper
from ..extractors.job_details_extractor import JobDetailsExtractor, load_selected_jobs


def export_selected_jobs(selected_jobs_df):
    """Export selected external jobs to a CSV file."""
    if not selected_jobs_df.empty:
        # Create selected jobs directory if it doesn't exist
        selected_dir = os.path.join('data', 'selected')
        os.makedirs(selected_dir, exist_ok=True)

        st.success(f"Exporting {len(selected_jobs_df)} selected jobs...")
        print(f"Selected jobs for export: {len(selected_jobs_df)}")

        # Clean up DataFrame before export
        export_df = selected_jobs_df.drop(columns=['selected', 'creationDate', 'expirationDate', 'companyName'], errors='ignore')

        # Export to CSV
        export_path = os.path.join(selected_dir, "selected_jobs_export.csv")
        export_df.to_csv(export_path, index=False)

        st.success(f"✅ Selected jobs exported to '{export_path}'")
        st.info(f"📁 File contains {len(export_df)} jobs with external application URLs")
    else:
        st.warning("No jobs selected for export.")


def display_scraper_status():
    """Display background scraper status."""
    scraper = get_background_scraper()
    status_info = scraper.get_status_info()

    status = status_info['status']
    progress = status_info['progress']

    # Create status container
    status_container = st.container()

    with status_container:
        if status == "running":
            st.info(f"🔄 **Scraping in progress:** {progress}")
            if status_info['start_time']:
                elapsed = (datetime.now() - status_info['start_time']).total_seconds()
                st.caption(f"⏱️ Running for {elapsed:.0f} seconds")
        elif status == "completed":
            st.success(f"✅ **Scraping completed:** {progress}")
            if status_info['duration']:
                st.caption(f"⏱️ Completed in {status_info['duration']:.1f} seconds")
        elif status == "failed":
            st.error(f"❌ **Scraping failed:** {status_info['error']}")
        elif status == "idle":
            st.info(f"💤 **Scraper idle:** {progress}")

    return status


def run_streamlit_dashboard():
    """Run the Streamlit dashboard to display job data."""
    # Page configuration
    st.set_page_config(
        page_title="PyJobber Dashboard",
        page_icon="💼",
        layout="wide"
    )

    st.title("💼 PyJobber - Job Listings Dashboard")

    # Initialize session state
    if 'selected_external_jobs' not in st.session_state:
        st.session_state.selected_external_jobs = pd.DataFrame()
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()

    # Display scraper status
    st.divider()
    scraper_status = display_scraper_status()
    st.divider()

    # Auto-refresh controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption(f"🕐 Last refreshed: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    with col3:
        if st.button("🔄 Refresh Now"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(5)
        st.session_state.last_refresh = datetime.now()
        st.rerun()

    # Check if CSV files exist
    if not csv_files_exist():
        st.warning("⚠️ No cached job data found.")
        if scraper_status == "running":
            st.info("🔄 Scraping is in progress. Data will appear when ready.")
        else:
            st.error("Please wait for the scraper to complete or run it manually:")
            st.code("python main.py --scrape")
        return

    # Load data
    df_bjobs, df_ejobs, external_jobs = load_jobs_from_csv()

    if df_bjobs is None or df_ejobs is None:
        st.error("Failed to load job data from CSV files.")
        return

    # Summary statistics
    st.subheader("📊 Summary Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Provider A Listings", len(df_bjobs))
    with col2:
        st.metric("Provider B Listings", len(df_ejobs))
    with col3:
        external_count = len(external_jobs) if external_jobs is not None else 0
        st.metric("External Job URLs", external_count)

    st.divider()

    # Display tabs for different data
    tab1, tab2, tab3, tab4 = st.tabs(["🔵 Provider A", "🟢 Provider B", "🔗 External Jobs", "📄 Job Details"])

    with tab1:
        st.header("🔵 Provider A Listings")
        st.caption(f"Total jobs: {len(df_bjobs)}")

        # Search filter
        search_term = st.text_input("🔍 Search by title or company", key="bjobs_search")
        if search_term:
            filtered_df = df_bjobs[
                df_bjobs['title'].str.contains(search_term, case=False, na=False) |
                df_bjobs['companyName'].str.contains(search_term, case=False, na=False)
            ]
            st.caption(f"Found {len(filtered_df)} matching jobs")
            st.dataframe(filtered_df, width='stretch', hide_index=True)
        else:
            st.dataframe(df_bjobs, width='stretch', hide_index=True)

    with tab2:
        st.header("🟢 Provider B Listings")
        st.caption(f"Total jobs: {len(df_ejobs)}")

        # Search filter
        search_term = st.text_input("🔍 Search by title", key="ejobs_search")
        if search_term:
            filtered_df = df_ejobs[
                df_ejobs['title'].str.contains(search_term, case=False, na=False)
            ]
            st.caption(f"Found {len(filtered_df)} matching jobs")
            st.dataframe(filtered_df, width='stretch', hide_index=True)
        else:
            st.dataframe(df_ejobs, width='stretch', hide_index=True)

    with tab3:
        st.header("🔗 External Job URLs")
        st.caption("Select jobs with external application URLs for export")

        if external_jobs is not None and len(external_jobs) > 0:
            # Add a selection column if it doesn't exist
            if 'selected' not in external_jobs.columns:
                external_jobs['selected'] = False

            # Search filter
            search_term = st.text_input("🔍 Search by title", key="external_search")
            if search_term:
                display_jobs = external_jobs[
                    external_jobs['title'].str.contains(search_term, case=False, na=False)
                ].copy()
                st.caption(f"Found {len(display_jobs)} matching jobs")
            else:
                display_jobs = external_jobs.copy()

            st.info(f"📋 Total external jobs: {len(external_jobs)} | Showing: {len(display_jobs)}")

            # Create editable dataframe
            edited_external_jobs = st.data_editor(
                display_jobs,
                column_config={
                    "selected": st.column_config.CheckboxColumn(
                        "✅ Select",
                        help="Select to export this job",
                        default=False
                    ),
                    "title": st.column_config.TextColumn(
                        "Job Title",
                        width="large"
                    ),
                    "ownApplyUrl": st.column_config.LinkColumn(
                        "Application URL",
                        width="medium"
                    )
                },
                width='stretch',
                hide_index=True,
                key="external_jobs_editor"
            )

            # Update session state with selected jobs DataFrame
            selected_mask = edited_external_jobs['selected']
            st.session_state.selected_external_jobs = edited_external_jobs[selected_mask].copy()

            # Display count of selected jobs
            selected_count = selected_mask.sum()

            # Action buttons
            col1, col2 = st.columns([3, 1])
            with col1:
                if selected_count > 0:
                    st.success(f"✅ {selected_count} job(s) selected for export")
                else:
                    st.info("ℹ️ Select jobs using the checkboxes above")

            with col2:
                export_button = st.button(
                    "📥 Export Selected",
                    disabled=selected_count == 0,
                    type="primary",
                    width='stretch'
                )

            # Show selected jobs preview if any are selected
            if selected_count > 0:
                with st.expander("👁️ Preview Selected Jobs", expanded=False):
                    preview_df = st.session_state.selected_external_jobs.drop('selected', axis=1, errors='ignore')
                    st.dataframe(preview_df, width='stretch', hide_index=True)

            # Export action
            if export_button:
                export_selected_jobs(st.session_state.selected_external_jobs)

        else:
            st.info("ℹ️ No jobs with external application URLs found.")
            st.caption("External jobs are those that have direct application links outside of job boards.")

    with tab4:
        st.header("📄 Job Details Extractor")
        st.caption("Extract detailed information from selected job URLs")

        # Initialize session state for extraction
        if 'extraction_results' not in st.session_state:
            st.session_state.extraction_results = []
        if 'extraction_in_progress' not in st.session_state:
            st.session_state.extraction_in_progress = False

        # Load selected jobs
        selected_jobs_path = "data/selected/selected_jobs_export.csv"

        if not os.path.exists(selected_jobs_path):
            st.warning("⚠️ No selected jobs found.")
            st.info("Please go to the 'External Jobs' tab and export some jobs first.")
        else:
            selected_df = load_selected_jobs(selected_jobs_path)

            if selected_df is not None and len(selected_df) > 0:
                st.success(f"✅ Found {len(selected_df)} selected jobs ready for extraction")

                # Display selected jobs
                with st.expander("👁️ View Selected Jobs", expanded=True):
                    display_df = selected_df[['id', 'title', 'ownApplyUrl']].copy()
                    st.dataframe(display_df, width='stretch', hide_index=True)

                st.divider()

                # Extraction controls
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown("### Extraction Options")
                    st.caption("The extractor will first attempt to parse HTML. If that fails, it will save the page as PDF and extract text from it.")

                with col2:
                    extract_button = st.button(
                        "🚀 Get Job Details",
                        type="primary",
                        width='stretch',
                        disabled=st.session_state.extraction_in_progress
                    )

                # Handle extraction
                if extract_button:
                    st.session_state.extraction_in_progress = True
                    st.session_state.extraction_results = []

                    # Create extractor
                    extractor = JobDetailsExtractor()

                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Extract each job
                    for idx, row in selected_df.iterrows():
                        progress = (idx + 1) / len(selected_df)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing job {idx + 1}/{len(selected_df)}: {row['title']}")

                        result = extractor.extract_job_details(
                            job_id=str(row['id']),
                            job_title=row['title'],
                            job_url=row['ownApplyUrl']
                        )

                        st.session_state.extraction_results.append(result)

                    progress_bar.progress(1.0)
                    status_text.text(f"✅ Completed processing {len(selected_df)} jobs!")

                    st.session_state.extraction_in_progress = False
                    st.rerun()

                # Display results if available
                if st.session_state.extraction_results:
                    st.divider()
                    st.markdown("### 📊 Extraction Results")

                    # Summary statistics
                    total_results = len(st.session_state.extraction_results)
                    successful = sum(1 for r in st.session_state.extraction_results if r['success'])
                    failed = total_results - successful

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Jobs", total_results)
                    with col2:
                        st.metric("Successful", successful, delta=None)
                    with col3:
                        st.metric("Failed", failed, delta=None)

                    st.divider()

                    # Display each result
                    for result in st.session_state.extraction_results:
                        with st.expander(f"{'✅' if result['success'] else '❌'} {result['job_title']}", expanded=False):
                            col1, col2 = st.columns([1, 3])

                            with col1:
                                st.markdown("**Status:**")
                                if result['success']:
                                    st.success(f"Success ({result['method'].upper()})")
                                else:
                                    st.error("Failed")

                                st.markdown("**URL:**")
                                st.markdown(f"[Link]({result['job_url']})")

                                if result['pdf_path']:
                                    st.markdown("**PDF:**")
                                    st.caption(result['pdf_path'])

                                if result['error']:
                                    st.markdown("**Error:**")
                                    st.error(result['error'])

                            with col2:
                                if result['markdown']:
                                    st.markdown("**Extracted Content:**")

                                    # Provide download button for markdown
                                    st.download_button(
                                        label="📥 Download Markdown",
                                        data=result['markdown'],
                                        file_name=f"job_{result['job_id']}.md",
                                        mime="text/markdown",
                                        key=f"download_{result['job_id']}"
                                    )

                                    # Display markdown content
                                    with st.container():
                                        st.markdown(result['markdown'])
                                else:
                                    st.warning("No content extracted")

                    # Clear results button
                    if st.button("🗑️ Clear Results"):
                        st.session_state.extraction_results = []
                        st.rerun()

            else:
                st.warning("⚠️ The selected jobs file is empty.")
                st.info("Please select and export jobs from the 'External Jobs' tab first.")