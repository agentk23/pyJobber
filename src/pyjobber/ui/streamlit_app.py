import streamlit as st
import pandas as pd
from ..storage.csv_handler import csv_files_exist, load_jobs_from_csv


def run_streamlit_dashboard():
    """Run the Streamlit dashboard to display job data."""
    st.title("PyJobber - Job Listings Dashboard")
    
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
            st.dataframe(external_jobs, use_container_width=True)
        else:
            st.info("No external job URLs found")