import streamlit as st
import pandas as pd
import os
from ..storage.csv_handler import csv_files_exist, load_jobs_from_csv

def export_selected_jobs(selected_jobs_df):
    """Export selected external jobs to a CSV file."""
    if not selected_jobs_df.empty:
        st.success(f"Exporting {len(selected_jobs_df)} selected jobs...")
        print(f"Selected jobs for export: {len(selected_jobs_df)}")
        selected_jobs_df = selected_jobs_df.drop(columns=['selected','creationDate','expirationDate', 'companyName'], errors='ignore')
        selected_jobs_df.to_csv(os.path.join('data/selected', "selected_jobs_export.csv"), index=False)
        st.success("Selected jobs exported to 'selected_jobs_export.csv'")
    else:
        st.warning("No jobs selected for export.")

def run_streamlit_dashboard():
    """Run the Streamlit dashboard to display job data."""
    st.title("PyJobber - Job Listings Dashboard")

    # Initialize session state for selected external jobs
    if 'selected_external_jobs' not in st.session_state:
        st.session_state.selected_external_jobs = pd.DataFrame()

    # Check if CSV files exist
    if not csv_files_exist():
        st.error("CSV files not found. Please run the scraper first:")
        st.code("python main.py --scrape")
        return

    # Load data
    df_bjobs, df_ejobs, external_jobs = load_jobs_from_csv()

    if df_bjobs is None or df_ejobs is None:
        st.error("Failed to load job data from CSV files.")
        return

    # Display tabs for different data
    tab1, tab2, tab3 = st.tabs(["BestJobs", "eJobs", "External Jobs"])
    with tab1:
        st.header("BestJobs Listings")
        st.write(f"Total jobs: {len(df_bjobs)}")
        st.dataframe(df_bjobs, use_container_width=True)
    
    with tab2:
        st.header("eJobs Listings")
        st.write(f"Total jobs: {len(df_ejobs)}")
        st.dataframe(df_ejobs, use_container_width=True)
    
    with tab3:
        st.header("External Job URLs")
        if external_jobs is not None and len(external_jobs) > 0:
            st.write(f"Total external jobs: {len(external_jobs)}")

            # Add a selection column if it doesn't exist
            if 'selected' not in external_jobs.columns:
                external_jobs['selected'] = False

            # Create editable dataframe
            edited_external_jobs = st.data_editor(
                external_jobs,
                column_config={
                    "selected": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select to export this job",
                        default=False
                    )
                },
                use_container_width=True,
                key="external_jobs_editor"
            )

            # Update session state with selected jobs DataFrame
            selected_mask = edited_external_jobs['selected']
            st.session_state.selected_external_jobs = edited_external_jobs[selected_mask].copy()

            # Display count of selected jobs
            selected_count = selected_mask.sum()
            st.write(f"Selected jobs: {selected_count}")

            # Show selected jobs preview if any are selected
            if selected_count > 0:
                st.subheader("Selected Jobs Preview")
                st.dataframe(st.session_state.selected_external_jobs.drop('selected', axis=1), use_container_width=True)

            # Export button
            if st.button("Export Selected Jobs", disabled=selected_count == 0):
                export_selected_jobs(st.session_state.selected_external_jobs)