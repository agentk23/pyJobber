import argparse
import lib.linkProvider.linkProvider as provider
import streamlit as st
import pandas as pd
import os

def streamlit_app():
    """Streamlit app to display job data"""
    st.title("PyJobber - Job Listings Dashboard")
    
    # Check if CSV files exist
    if not (os.path.exists('bjobs.csv') and os.path.exists('ejobs.csv')):
        st.error("CSV files not found. Please run the scraper first:")
        st.code("python main.py --scrape")
        return
    
    # Load data
    dfBJobs = pd.read_csv('bjobs.csv')
    dfEJobs = pd.read_csv('ejobs.csv')
    externalJobs = None
    if os.path.exists('externalJobs.csv'):
        externalJobs = pd.read_csv('externalJobs.csv')
    
    # Display tabs for different data
    tab1, tab2, tab3 = st.tabs(["BestJobs", "eJobs", "External Jobs"])
    
    with tab1:
        st.header("BestJobs Listings")
        st.write(f"Total jobs: {len(dfBJobs)}")
        st.dataframe(dfBJobs, use_container_width=True)
    
    with tab2:
        st.header("eJobs Listings")
        st.write(f"Total jobs: {len(dfEJobs)}")
        st.dataframe(dfEJobs, use_container_width=True)
    
    with tab3:
        st.header("External Job URLs")
        if externalJobs is not None and len(externalJobs) > 0:
            st.write(f"Total external jobs: {len(externalJobs)}")
            st.dataframe(externalJobs, use_container_width=True)
        else:
            st.info("No external job URLs found")

def main():
    parser = argparse.ArgumentParser(description="PyJobber - Job scraper and viewer")
    parser.add_argument('--scrape', action='store_true', help='Run the job scraper')
    parser.add_argument('--streamlit', action='store_true', help='Run in Streamlit mode (use: streamlit run main.py -- --streamlit)')
    
    args = parser.parse_args()
    
    if args.streamlit:
        streamlit_app()
    elif args.scrape:
        provider.run_script_or_read_csv()
    else:
        # Default behavior - just run scraper
        provider.run_script_or_read_csv()

if __name__ == "__main__":
    main()
