import time
import requests
import pandas as pd
from typing import Optional

# 1. Parse the data from the API
# ------------------------------
# returns a list of dictionaries -> each dictionary is a job
# each dictionary has the following keys: id, slug, title, companyName, active, ownApplyUrl
# iterate through the list and add them to a dataframe

# dfBjobs.to_csv('bjobs.csv', index=False)
# returns a list of dictionaries -> each dictionary is a job
# id, title, slug, creationDate, expirationDate, company['name'], externalUrl
def performBjobsRequest(pageNumber=1, limit=24):
    bestjobs_url = f'https://api.bestjobs.eu/v1/jobs?offset=0&limit={limit}&remote=1'
    response = requests.get(bestjobs_url)

    result = response.json()
    limit = result['total']
    bestjobs_url = f'https://api.bestjobs.eu/v1/jobs?offset=0&limit={limit}&remote=1'
    time.sleep(5)
    response = requests.get(bestjobs_url)
    result = response.json()
    return result['items']

def performEjobsRequest(pageNumber=1):
    ejobs_url = f'https://api.ejobs.ro/jobs?page={pageNumber}&pageSize=100&filters.cities=381&filters.cities=1&filters.careerLevels=10&filters.careerLevels=3&filters.careerLevels=4&sort=suitability'
    response = requests.get(ejobs_url)

    morePagesFollow = response.json()['morePagesFollow']
    results = []
    while morePagesFollow:
        results.extend(response.json()['jobs'])
        pageNumber += 1
        time.sleep(5)
        ejobs_url = f'https://api.ejobs.ro/jobs?page={pageNumber}&pageSize=100&filters.cities=381&filters.cities=1&filters.careerLevels=10&filters.careerLevels=3&filters.careerLevels=4&sort=suitability'
        response = requests.get(ejobs_url)
        try:
            morePagesFollow = response.json()['morePagesFollow']
        except:
            break
    return results

def performAPICalls():
    resultsBjobs = performBjobsRequest()
    dfBjobs = pd.DataFrame(resultsBjobs)
    dfBjobs = dfBjobs[['id', 'slug', 'title', 'companyName', 'active', 'ownApplyUrl']]

    resultsEjobs = performEjobsRequest()
    dfEjobs = pd.DataFrame(resultsEjobs)
    dfEjobs = dfEjobs[['id', 'title', 'slug', 'creationDate', 'expirationDate', 'externalUrl']]
    dfEjobs.sort_values(by='creationDate')

    dfBjobs = filterDataFrameFromBannedWords(dfBjobs)
    dfEjobs = filterDataFrameFromBannedWords(dfEjobs)

    bJobsLinks = createIndividualLinks("bjobs", dfBjobs)
    eJobsLinks = createIndividualLinks("ejobs", dfEjobs)

    dfBjobs = dfBjobs[['title', 'companyName', 'ownApplyUrl']]
    dfEjobs = dfEjobs[['title', 'creationDate', 'expirationDate', 'externalUrl']]
    dfEjobs.rename(columns={"externalUrl":"ownApplyUrl"})
    
    dfExternalEjobs = extractJobsWithExternalApplyLinks(dfEjobs)
    dfExternalBjobs = extractJobsWithExternalApplyLinks(dfBjobs)
    externalJobs:Optional[pd.DataFrame] = pd.concat([dfExternalEjobs, dfExternalBjobs]).to_csv('externalJobs.csv', index=False)

    dfBjobs = pd.concat([dfBjobs, bJobsLinks], axis=1)
    dfEjobs = pd.concat([dfEjobs, eJobsLinks], axis=1)

    return dfBjobs, dfEjobs, externalJobs

def createIndividualLinks(prefix, filteredJobs):
    if prefix == 'bjobs':
        return filteredJobs.apply(lambda x: f'https://www.bestjobs.eu/loc-de-munca/{x["slug"]}', axis=1)
    if prefix == 'ejobs':
        return filteredJobs.apply(lambda x: f'https://www.ejobs.ro/user/locuri-de-munca/{x["slug"]}/{x["id"]}', axis=1)
    return None

def filterDataFrameFromBannedWords(df):
    bannedWords = []
    with open('bannedWords.txt', 'r') as file:
        bannedWords = [line.strip() for line in file if line.strip()]
    mask = df['title'].apply(lambda x: not any(banned_word.lower() in x.lower() for banned_word in bannedWords))
    return df[mask]

def extractJobsWithExternalApplyLinks(df:Optional[pd.DataFrame]):
    return df[df['ownApplyUrl'].notna()] if df is not None else None

def writeDataFrameToCSV(df, filename):
    df.to_csv(filename, index=False)