import os
import sys
from datetime import datetime, timedelta
import pandas as pd
# import streamlit as st
import jobs as jb


def check_last_run(timestamp_file="last_run.txt"):
    if not os.path.exists(timestamp_file):
        # First time running - create timestamp file and return True
        update_timestamp(timestamp_file)
        return True

    try:
        with open(timestamp_file, 'r') as f:
            last_run_str = f.read().strip()

        # Parse the timestamp
        last_run = datetime.fromisoformat(last_run_str)
        current_time = datetime.now()

        # Check if 24 hours have passed
        time_diff = current_time - last_run
        if time_diff >= timedelta(days=1):
            update_timestamp(timestamp_file)
            return True
        else:
            hours_remaining = 24 - (time_diff.total_seconds() / 3600)
            print(f"Script last ran {time_diff} ago.")
            print(f"Need to wait {hours_remaining:.1f} more hours before next run.")
            return False

    except (ValueError, IOError) as e:
        print(f"Error reading timestamp file: {e}")
        update_timestamp(timestamp_file)
        return True

def update_timestamp(timestamp_file="last_run.txt"):
    try:
        with open(timestamp_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except IOError as e:
        print(f"Error writing timestamp file: {e}")

# def streamlit_run(dfBjobsMerged, dfEjobsMerged, externalJobs):
#     st.title("DataFrame Display")
#     st.write("Displaying the Bjobs DataFrame:")
#     st.dataframe(dfBjobsMerged)
#     st.write("Displaying the Ejobs DataFrame:")
#     st.dataframe(dfEjobsMerged)
#     st.write("Displaying the External Jobs DataFrame:")
#     st.dataframe(externalJobs)  

def main():
    if check_last_run():
        print("24+ hours have passed. Running script...")
        dfBJobs, dfEJobs, externalJobs = jb.performAPICalls()
        dfBJobs.to_csv('bjobs.csv', index=False)
        dfEJobs.to_csv('ejobs.csv', index=False)
        print(externalJobs)
        if externalJobs is not None:
            externalJobs.to_csv('externalJobs', index=False)
        update_timestamp()
        
    else:
        if os.path.exists('bjobs.csv') and os.path.exists('ejobs.csv'):
            dfBJobs = pd.read_csv('bjobs.csv')
            dfEJobs = pd.read_csv('ejobs.csv')
            externalJobs = pd.read_csv('externalJobs.csv')
            print("CSV files found. Displaying dataframes.")
        else:
            print("No CSV files found. Please run the script after 24 hours or manually.")
            sys.exit(0)
    # streamlit_run(dfBJobs, dfEJobs)

if __name__ == "__main__":
    main()


