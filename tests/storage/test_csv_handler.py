"""Tests for CSV storage functionality."""
import os
import pytest
import pandas as pd
from src.pyjobber.storage.csv_handler import (
    save_jobs_to_csv,
    load_jobs_from_csv,
    csv_files_exist
)


class TestSaveJobsToCSV:
    """Tests for save_jobs_to_csv function."""

    def test_save_jobs_creates_cache_directory(self, tmp_path):
        """Test that save_jobs_to_csv creates cache directory if it doesn't exist."""
        cache_dir = tmp_path / "new_cache"
        df_bjobs = pd.DataFrame([{"title": "Dev", "companyName": "Corp", "ownApplyUrl": "", "link": "url"}])
        df_ejobs = pd.DataFrame([{"title": "Dev", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "", "link": "url"}])

        save_jobs_to_csv(df_bjobs, df_ejobs, cache_dir=str(cache_dir))

        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_save_jobs_creates_csv_files(self, temp_cache_dir):
        """Test that save_jobs_to_csv creates the expected CSV files."""
        df_bjobs = pd.DataFrame([{"title": "Dev", "companyName": "Corp", "ownApplyUrl": "", "link": "url"}])
        df_ejobs = pd.DataFrame([{"title": "Dev", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "", "link": "url"}])

        save_jobs_to_csv(df_bjobs, df_ejobs, cache_dir=temp_cache_dir)

        assert os.path.exists(os.path.join(temp_cache_dir, 'bjobs.csv'))
        assert os.path.exists(os.path.join(temp_cache_dir, 'ejobs.csv'))

    def test_save_jobs_with_external_jobs(self, temp_cache_dir):
        """Test saving with external jobs DataFrame."""
        df_bjobs = pd.DataFrame([{"title": "Dev", "companyName": "Corp", "ownApplyUrl": "", "link": "url"}])
        df_ejobs = pd.DataFrame([{"title": "Dev", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "", "link": "url"}])
        df_external = pd.DataFrame([{"title": "Ext Job", "ownApplyUrl": "https://external.com"}])

        save_jobs_to_csv(df_bjobs, df_ejobs, df_external, cache_dir=temp_cache_dir)

        assert os.path.exists(os.path.join(temp_cache_dir, 'bjobs.csv'))
        assert os.path.exists(os.path.join(temp_cache_dir, 'ejobs.csv'))
        assert os.path.exists(os.path.join(temp_cache_dir, 'externalJobs.csv'))

    def test_save_jobs_without_external_jobs(self, temp_cache_dir):
        """Test saving without external jobs (None)."""
        df_bjobs = pd.DataFrame([{"title": "Dev", "companyName": "Corp", "ownApplyUrl": "", "link": "url"}])
        df_ejobs = pd.DataFrame([{"title": "Dev", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "", "link": "url"}])

        save_jobs_to_csv(df_bjobs, df_ejobs, external_jobs=None, cache_dir=temp_cache_dir)

        assert os.path.exists(os.path.join(temp_cache_dir, 'bjobs.csv'))
        assert os.path.exists(os.path.join(temp_cache_dir, 'ejobs.csv'))
        assert not os.path.exists(os.path.join(temp_cache_dir, 'externalJobs.csv'))

    def test_save_jobs_empty_dataframes(self, temp_cache_dir):
        """Test saving empty DataFrames."""
        df_bjobs = pd.DataFrame(columns=["title", "companyName", "ownApplyUrl", "link"])
        df_ejobs = pd.DataFrame(columns=["title", "creationDate", "expirationDate", "ownApplyUrl", "link"])

        save_jobs_to_csv(df_bjobs, df_ejobs, cache_dir=temp_cache_dir)

        assert os.path.exists(os.path.join(temp_cache_dir, 'bjobs.csv'))
        assert os.path.exists(os.path.join(temp_cache_dir, 'ejobs.csv'))

        # Verify files are valid CSV with headers
        loaded_bjobs = pd.read_csv(os.path.join(temp_cache_dir, 'bjobs.csv'))
        loaded_ejobs = pd.read_csv(os.path.join(temp_cache_dir, 'ejobs.csv'))

        assert len(loaded_bjobs) == 0
        assert len(loaded_ejobs) == 0
        assert list(loaded_bjobs.columns) == ["title", "companyName", "ownApplyUrl", "link"]

    def test_save_jobs_overwrites_existing(self, temp_cache_dir):
        """Test that save_jobs_to_csv overwrites existing files."""
        # Save first set of data
        df_bjobs1 = pd.DataFrame([{"title": "Job1", "companyName": "Corp1", "ownApplyUrl": "", "link": "url1"}])
        df_ejobs1 = pd.DataFrame([{"title": "Job1", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "", "link": "url1"}])
        save_jobs_to_csv(df_bjobs1, df_ejobs1, cache_dir=temp_cache_dir)

        # Save second set of data
        df_bjobs2 = pd.DataFrame([{"title": "Job2", "companyName": "Corp2", "ownApplyUrl": "", "link": "url2"}])
        df_ejobs2 = pd.DataFrame([{"title": "Job2", "creationDate": "2024-01-02", "expirationDate": "2024-02-02", "ownApplyUrl": "", "link": "url2"}])
        save_jobs_to_csv(df_bjobs2, df_ejobs2, cache_dir=temp_cache_dir)

        # Load and verify second set is saved
        loaded_bjobs = pd.read_csv(os.path.join(temp_cache_dir, 'bjobs.csv'))
        assert len(loaded_bjobs) == 1
        assert loaded_bjobs.iloc[0]['title'] == "Job2"


class TestLoadJobsFromCSV:
    """Tests for load_jobs_from_csv function."""

    def test_load_jobs_success(self, temp_cache_dir):
        """Test successful loading of job CSVs."""
        # Create test CSV files
        df_bjobs = pd.DataFrame([
            {"title": "Python Dev", "companyName": "Tech Corp", "ownApplyUrl": "url1", "link": "link1"},
            {"title": "Java Dev", "companyName": "Dev Inc", "ownApplyUrl": "url2", "link": "link2"}
        ])
        df_ejobs = pd.DataFrame([
            {"title": "Backend Dev", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "url3", "link": "link3"}
        ])

        df_bjobs.to_csv(os.path.join(temp_cache_dir, 'bjobs.csv'), index=False)
        df_ejobs.to_csv(os.path.join(temp_cache_dir, 'ejobs.csv'), index=False)

        # Load
        loaded_bjobs, loaded_ejobs, loaded_external = load_jobs_from_csv(temp_cache_dir)

        assert len(loaded_bjobs) == 2
        assert len(loaded_ejobs) == 1
        assert loaded_external is None
        assert loaded_bjobs.iloc[0]['title'] == "Python Dev"
        assert loaded_ejobs.iloc[0]['title'] == "Backend Dev"

    def test_load_jobs_with_external(self, temp_cache_dir):
        """Test loading jobs with external jobs file."""
        df_bjobs = pd.DataFrame([{"title": "Dev", "companyName": "Corp", "ownApplyUrl": "", "link": "url"}])
        df_ejobs = pd.DataFrame([{"title": "Dev", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "", "link": "url"}])
        df_external = pd.DataFrame([{"title": "External Job", "ownApplyUrl": "https://external.com"}])

        df_bjobs.to_csv(os.path.join(temp_cache_dir, 'bjobs.csv'), index=False)
        df_ejobs.to_csv(os.path.join(temp_cache_dir, 'ejobs.csv'), index=False)
        df_external.to_csv(os.path.join(temp_cache_dir, 'externalJobs.csv'), index=False)

        loaded_bjobs, loaded_ejobs, loaded_external = load_jobs_from_csv(temp_cache_dir)

        assert loaded_external is not None
        assert len(loaded_external) == 1
        assert loaded_external.iloc[0]['title'] == "External Job"

    def test_load_jobs_missing_files(self, temp_cache_dir):
        """Test loading when CSV files don't exist."""
        loaded_bjobs, loaded_ejobs, loaded_external = load_jobs_from_csv(temp_cache_dir)

        assert loaded_bjobs is None
        assert loaded_ejobs is None
        assert loaded_external is None

    def test_load_jobs_only_bjobs_exists(self, temp_cache_dir):
        """Test loading when only bjobs.csv exists."""
        df_bjobs = pd.DataFrame([{"title": "Dev", "companyName": "Corp", "ownApplyUrl": "", "link": "url"}])
        df_bjobs.to_csv(os.path.join(temp_cache_dir, 'bjobs.csv'), index=False)

        loaded_bjobs, loaded_ejobs, loaded_external = load_jobs_from_csv(temp_cache_dir)

        # Should return None for all if both required files don't exist
        assert loaded_bjobs is None
        assert loaded_ejobs is None
        assert loaded_external is None

    def test_load_jobs_only_ejobs_exists(self, temp_cache_dir):
        """Test loading when only ejobs.csv exists."""
        df_ejobs = pd.DataFrame([{"title": "Dev", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "", "link": "url"}])
        df_ejobs.to_csv(os.path.join(temp_cache_dir, 'ejobs.csv'), index=False)

        loaded_bjobs, loaded_ejobs, loaded_external = load_jobs_from_csv(temp_cache_dir)

        # Should return None for all if both required files don't exist
        assert loaded_bjobs is None
        assert loaded_ejobs is None
        assert loaded_external is None

    def test_load_jobs_empty_csv_files(self, temp_cache_dir):
        """Test loading empty CSV files."""
        df_bjobs = pd.DataFrame(columns=["title", "companyName", "ownApplyUrl", "link"])
        df_ejobs = pd.DataFrame(columns=["title", "creationDate", "expirationDate", "ownApplyUrl", "link"])

        df_bjobs.to_csv(os.path.join(temp_cache_dir, 'bjobs.csv'), index=False)
        df_ejobs.to_csv(os.path.join(temp_cache_dir, 'ejobs.csv'), index=False)

        loaded_bjobs, loaded_ejobs, loaded_external = load_jobs_from_csv(temp_cache_dir)

        assert len(loaded_bjobs) == 0
        assert len(loaded_ejobs) == 0
        assert loaded_external is None


class TestCSVFilesExist:
    """Tests for csv_files_exist function."""

    def test_csv_files_exist_both_present(self, temp_cache_dir):
        """Test when both required CSV files exist."""
        df_bjobs = pd.DataFrame([{"title": "Dev"}])
        df_ejobs = pd.DataFrame([{"title": "Dev"}])

        df_bjobs.to_csv(os.path.join(temp_cache_dir, 'bjobs.csv'), index=False)
        df_ejobs.to_csv(os.path.join(temp_cache_dir, 'ejobs.csv'), index=False)

        assert csv_files_exist(temp_cache_dir) is True

    def test_csv_files_exist_none_present(self, temp_cache_dir):
        """Test when no CSV files exist."""
        assert csv_files_exist(temp_cache_dir) is False

    def test_csv_files_exist_only_bjobs(self, temp_cache_dir):
        """Test when only bjobs.csv exists."""
        df_bjobs = pd.DataFrame([{"title": "Dev"}])
        df_bjobs.to_csv(os.path.join(temp_cache_dir, 'bjobs.csv'), index=False)

        assert csv_files_exist(temp_cache_dir) is False

    def test_csv_files_exist_only_ejobs(self, temp_cache_dir):
        """Test when only ejobs.csv exists."""
        df_ejobs = pd.DataFrame([{"title": "Dev"}])
        df_ejobs.to_csv(os.path.join(temp_cache_dir, 'ejobs.csv'), index=False)

        assert csv_files_exist(temp_cache_dir) is False

    def test_csv_files_exist_with_external(self, temp_cache_dir):
        """Test when external jobs file also exists (should still return True)."""
        df_bjobs = pd.DataFrame([{"title": "Dev"}])
        df_ejobs = pd.DataFrame([{"title": "Dev"}])
        df_external = pd.DataFrame([{"title": "Ext"}])

        df_bjobs.to_csv(os.path.join(temp_cache_dir, 'bjobs.csv'), index=False)
        df_ejobs.to_csv(os.path.join(temp_cache_dir, 'ejobs.csv'), index=False)
        df_external.to_csv(os.path.join(temp_cache_dir, 'externalJobs.csv'), index=False)

        assert csv_files_exist(temp_cache_dir) is True

    def test_csv_files_exist_nonexistent_directory(self):
        """Test with a directory that doesn't exist."""
        assert csv_files_exist("/nonexistent/cache/dir") is False


class TestCSVHandlerIntegration:
    """Integration tests for CSV handler functionality."""

    def test_save_and_load_roundtrip(self, temp_cache_dir):
        """Test complete save and load cycle."""
        # Create sample data
        df_bjobs_original = pd.DataFrame([
            {"title": "Python Developer", "companyName": "Tech Corp", "ownApplyUrl": "url1", "link": "link1"},
            {"title": "Java Developer", "companyName": "Dev Inc", "ownApplyUrl": "url2", "link": "link2"}
        ])
        df_ejobs_original = pd.DataFrame([
            {"title": "Backend Developer", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "url3", "link": "link3"}
        ])
        df_external_original = pd.DataFrame([
            {"title": "External Job", "ownApplyUrl": "https://external.com"}
        ])

        # Save
        save_jobs_to_csv(df_bjobs_original, df_ejobs_original, df_external_original, cache_dir=temp_cache_dir)

        # Verify files exist
        assert csv_files_exist(temp_cache_dir) is True

        # Load
        df_bjobs_loaded, df_ejobs_loaded, df_external_loaded = load_jobs_from_csv(temp_cache_dir)

        # Verify data integrity
        assert len(df_bjobs_loaded) == 2
        assert len(df_ejobs_loaded) == 1
        assert len(df_external_loaded) == 1

        assert df_bjobs_loaded.iloc[0]['title'] == "Python Developer"
        assert df_bjobs_loaded.iloc[1]['title'] == "Java Developer"
        assert df_ejobs_loaded.iloc[0]['title'] == "Backend Developer"
        assert df_external_loaded.iloc[0]['title'] == "External Job"

    def test_multiple_save_operations(self, temp_cache_dir):
        """Test multiple save operations overwrite correctly."""
        # First save
        df1 = pd.DataFrame([{"title": "Job1", "companyName": "Corp1", "ownApplyUrl": "", "link": ""}])
        df2 = pd.DataFrame([{"title": "Job1", "creationDate": "2024-01-01", "expirationDate": "2024-02-01", "ownApplyUrl": "", "link": ""}])
        save_jobs_to_csv(df1, df2, cache_dir=temp_cache_dir)

        # Second save with different data
        df3 = pd.DataFrame([
            {"title": "Job2", "companyName": "Corp2", "ownApplyUrl": "", "link": ""},
            {"title": "Job3", "companyName": "Corp3", "ownApplyUrl": "", "link": ""}
        ])
        df4 = pd.DataFrame([{"title": "Job2", "creationDate": "2024-01-02", "expirationDate": "2024-02-02", "ownApplyUrl": "", "link": ""}])
        save_jobs_to_csv(df3, df4, cache_dir=temp_cache_dir)

        # Load and verify latest save
        loaded_bjobs, loaded_ejobs, _ = load_jobs_from_csv(temp_cache_dir)

        assert len(loaded_bjobs) == 2
        assert len(loaded_ejobs) == 1
        assert "Job2" in loaded_bjobs['title'].values
        assert "Job3" in loaded_bjobs['title'].values
