import os
import pandas as pd


def load_banned_words(banned_words_file="data/banned_words.txt"):
    """Load banned words from file."""
    try:
        with open(banned_words_file, 'r') as file:
            banned_words = [line.strip() for line in file if line.strip()]
        print(f"[INFO] Loaded {len(banned_words)} banned words")
        return banned_words
    except FileNotFoundError:
        print(f"[ERROR] {banned_words_file} not found")
        return []
    except Exception as e:
        print(f"[ERROR] Error loading banned words: {e}")
        return []


def filter_jobs_by_banned_words(df, banned_words_file="data/banned_words.txt"):
    """Filter DataFrame by removing jobs with banned words in title."""
    try:
        banned_words = load_banned_words(banned_words_file)
        
        if len(df) == 0 or not banned_words:
            print("[INFO] Empty DataFrame or no banned words, skipping filtering")
            return df
        
        mask = df['title'].apply(
            lambda x: not any(banned_word.lower() in x.lower() for banned_word in banned_words)
        )
        filtered_df = df[mask]
        filtered_count = len(df) - len(filtered_df)
        
        if filtered_count > 0:
            print(f"[INFO] Filtered out {filtered_count} jobs containing banned words")
        else:
            print("[INFO] No jobs filtered by banned words")
        
        return filtered_df
        
    except Exception as e:
        print(f"[ERROR] Error during word filtering: {e}, returning unfiltered data")
        return df