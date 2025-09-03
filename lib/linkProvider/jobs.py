import time
import requests
import pandas as pd
from typing import Optional, Tuple

# 1. Parse the data from the API
# ------------------------------
# returns a list of dictionaries -> each dictionary is a job
# each dictionary has the following keys: id, slug, title, companyName, active, ownApplyUrl
# iterate through the list and add them to a dataframe

# dfBjobs.to_csv('bjobs.csv', index=False)
# returns a list of dictionaries -> each dictionary is a job
# id, title, slug, creationDate, expirationDate, company['name'], externalUrl
def performBjobsRequest(pageNumber=1, limit=24, remote=False):
    print("[INFO] Starting BestJobs API request...")
    try:
        bestjobs_url = f'https://api.bestjobs.eu/v1/jobs?offset=0&limit={limit}&remote={(1 if remote else 0)}'

        print(f"[INFO] Making initial request to: {bestjobs_url}")
        response = requests.get(bestjobs_url, timeout=30)
        response.raise_for_status()

        result = response.json()
        if 'total' not in result:
            raise KeyError("'total' key not found in BestJobs API response")
        
        total_jobs = result['total']
        print(f"[INFO] Found {total_jobs} total jobs, fetching all...")
        
        bestjobs_url = f'https://api.bestjobs.eu/v1/jobs?offset=0&limit={total_jobs}&remote=1'
        print(f"[INFO] Making full request to: {bestjobs_url}")
        time.sleep(5)
        response = requests.get(bestjobs_url, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'items' not in result:
            raise KeyError("'items' key not found in BestJobs API response")
        
        jobs = result['items']
        print(f"[SUCCESS] Retrieved {len(jobs)} jobs from BestJobs")
        return jobs
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error while fetching BestJobs: {e}")
        raise
    except KeyError as e:
        print(f"[ERROR] Missing key in BestJobs API response: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in BestJobs request: {e}")
        raise

def performEjobsRequest(pageNumber=1):
    print("[INFO] Starting eJobs API request...")
    page = pageNumber
    results = []
    
    try:
        ejobs_url = f'https://api.ejobs.ro/jobs?page={page}&pageSize=100&filters.cities=381&filters.cities=1&filters.careerLevels=10&filters.careerLevels=3&filters.careerLevels=4&sort=suitability'
        print(f"[INFO] Making initial request to eJobs, page {page}")
        response = requests.get(ejobs_url, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        print(f"[DEBUG] eJobs response keys: {list(response_data.keys())}")
        
        # Check if the expected keys exist
        if 'jobs' not in response_data:
            print(f"[ERROR] 'jobs' key not found in eJobs API response. Available keys: {list(response_data.keys())}")
            return []
            
        if 'morePagesFollow' not in response_data:
            print("[WARNING] 'morePagesFollow' key not found, assuming single page")
            jobs = response_data['jobs']
            print(f"[SUCCESS] Retrieved {len(jobs)} jobs from eJobs (single page)")
            return jobs
        
        morePagesFollow = response_data['morePagesFollow']
        print(f"[INFO] More pages follow: {morePagesFollow}")
        
        while morePagesFollow:
            current_jobs = response_data['jobs']
            results.extend(current_jobs)
            print(f"[INFO] Added {len(current_jobs)} jobs from page {page}, total so far: {len(results)}")
            
            page += 1
            time.sleep(5)
            ejobs_url = f'https://api.ejobs.ro/jobs?page={page}&pageSize=100&filters.cities=381&filters.cities=1&filters.careerLevels=10&filters.careerLevels=3&filters.careerLevels=4&sort=suitability'
            print(f"[INFO] Fetching page {page}...")
            
            response = requests.get(ejobs_url, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            
            if 'jobs' not in response_data:
                print(f"[WARNING] 'jobs' key missing on page {page}, stopping pagination")
                break
                
            morePagesFollow = response_data.get('morePagesFollow', False)
            
        print(f"[SUCCESS] Retrieved {len(results)} total jobs from eJobs")
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error while fetching eJobs: {e}")
        raise
    except KeyError as e:
        print(f"[ERROR] Missing key in eJobs API response: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in eJobs request: {e}")
        raise

def performAPICalls() -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    print("[INFO] Starting job scraping process...")
    
    try:
        # Fetch BestJobs data
        print("\n=== FETCHING BESTJOBS DATA ===")
        resultsBjobs = performBjobsRequest()
        dfBjobs = pd.DataFrame(resultsBjobs)
        
        required_bjobs_cols = ['id', 'slug', 'title', 'companyName', 'active', 'ownApplyUrl']
        missing_cols = [col for col in required_bjobs_cols if col not in dfBjobs.columns]
        if missing_cols:
            print(f"[WARNING] Missing columns in BestJobs data: {missing_cols}")
            print(f"[INFO] Available columns: {list(dfBjobs.columns)}")
        
        dfBjobs = dfBjobs[required_bjobs_cols]
        print(f"[INFO] Processed {len(dfBjobs)} BestJobs entries")

        # Fetch eJobs data
        print("\n=== FETCHING EJOBS DATA ===")
        resultsEjobs = performEjobsRequest()
        dfEjobs = pd.DataFrame(resultsEjobs)
        
        if len(dfEjobs) == 0:
            print("[WARNING] No eJobs data retrieved, creating empty DataFrame")
            dfEjobs = pd.DataFrame(columns=['id', 'title', 'slug', 'creationDate', 'expirationDate', 'externalUrl'])
        else:
            required_ejobs_cols = ['id', 'title', 'slug', 'creationDate', 'expirationDate', 'externalUrl']
            missing_cols = [col for col in required_ejobs_cols if col not in dfEjobs.columns]
            if missing_cols:
                print(f"[WARNING] Missing columns in eJobs data: {missing_cols}")
                print(f"[INFO] Available columns: {list(dfEjobs.columns)}")
            
            dfEjobs = dfEjobs[required_ejobs_cols]
            dfEjobs = dfEjobs.sort_values(by='creationDate')
            print(f"[INFO] Processed {len(dfEjobs)} eJobs entries")

        # Apply word filtering
        print("\n=== APPLYING WORD FILTERS ===")
        initial_bjobs_count = len(dfBjobs)
        initial_ejobs_count = len(dfEjobs)
        
        dfBjobs = filterDataFrameFromBannedWords(dfBjobs)
        dfEjobs = filterDataFrameFromBannedWords(dfEjobs)
        
        print(f"[INFO] BestJobs: {initial_bjobs_count} -> {len(dfBjobs)} jobs (filtered {initial_bjobs_count - len(dfBjobs)})")
        print(f"[INFO] eJobs: {initial_ejobs_count} -> {len(dfEjobs)} jobs (filtered {initial_ejobs_count - len(dfEjobs)})")

        # Generate links
        print("\n=== GENERATING LINKS ===")
        bJobsLinks = createIndividualLinks("bjobs", dfBjobs)
        eJobsLinks = createIndividualLinks("ejobs", dfEjobs)

        # Prepare final DataFrames
        print("\n=== PREPARING FINAL DATA ===")
        dfBjobs = dfBjobs[['title', 'companyName', 'ownApplyUrl']]
        dfEjobs = dfEjobs[['title', 'creationDate', 'expirationDate', 'externalUrl']]
        dfEjobs = dfEjobs.rename(columns={"externalUrl":"ownApplyUrl"})
        
        # Create external jobs DataFrame
        dfExternalEjobs = dfEjobs[dfEjobs['ownApplyUrl'].notna() & (dfEjobs['ownApplyUrl'] != '')]
        dfExternalBjobs = dfBjobs[dfBjobs['ownApplyUrl'].notna() & (dfBjobs['ownApplyUrl'] != '')]
        
        if len(dfExternalEjobs) > 0 or len(dfExternalBjobs) > 0:
            externalJobs = pd.concat([dfExternalEjobs, dfExternalBjobs], ignore_index=True)
            print(f"[INFO] Created external jobs DataFrame with {len(externalJobs)} entries")
        else:
            externalJobs = None
            print("[INFO] No external job URLs found")

        # Add generated links to DataFrames
        dfBjobs = pd.concat([dfBjobs, bJobsLinks], axis=1)
        dfEjobs = pd.concat([dfEjobs, eJobsLinks], axis=1)
        
        print("\n[SUCCESS] Job scraping completed successfully!")
        print(f"[SUMMARY] Final counts - BestJobs: {len(dfBjobs)}, eJobs: {len(dfEjobs)}")
        
        return dfBjobs, dfEjobs, externalJobs
        
    except Exception as e:
        print(f"[ERROR] Fatal error in performAPICalls: {e}")
        raise

def createIndividualLinks(prefix, filteredJobs):
    if prefix == 'bjobs':
        return filteredJobs.apply(lambda x: f'https://www.bestjobs.eu/loc-de-munca/{x["slug"]}', axis=1)
    if prefix == 'ejobs':
        return filteredJobs.apply(lambda x: f'https://www.ejobs.ro/user/locuri-de-munca/{x["slug"]}/{x["id"]}', axis=1)
    return None

def filterDataFrameFromBannedWords(df):
    try:
        print("[INFO] Loading banned words filter...")
        bannedWords = []
        with open('bannedWords.txt', 'r') as file:
            bannedWords = [line.strip() for line in file if line.strip()]
        print(f"[INFO] Loaded {len(bannedWords)} banned words")
        
        if len(df) == 0:
            print("[INFO] Empty DataFrame, skipping word filtering")
            return df
            
        mask = df['title'].apply(lambda x: not any(banned_word.lower() in x.lower() for banned_word in bannedWords))
        filtered_df = df[mask]
        filtered_count = len(df) - len(filtered_df)
        
        if filtered_count > 0:
            print(f"[INFO] Filtered out {filtered_count} jobs containing banned words")
        else:
            print("[INFO] No jobs filtered by banned words")
            
        return filtered_df
        
    except FileNotFoundError:
        print("[ERROR] bannedWords.txt not found, skipping word filtering")
        return df
    except Exception as e:
        print(f"[ERROR] Error during word filtering: {e}, returning unfiltered data")
        return df



def writeDataFrameToCSV(df, filename):
    df.to_csv(filename, index=False)