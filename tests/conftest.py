"""Shared test fixtures for PyJobber tests."""
import os
import pytest
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory for tests."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return str(data_dir)


@pytest.fixture
def banned_words_file(tmp_path):
    """Create a temporary banned words file with sample data."""
    banned_words_path = tmp_path / "banned_words.txt"
    banned_words = ["sales", "marketing", "manager", "consultant"]
    banned_words_path.write_text("\n".join(banned_words))
    return str(banned_words_path)


@pytest.fixture
def empty_banned_words_file(tmp_path):
    """Create an empty banned words file."""
    banned_words_path = tmp_path / "banned_words_empty.txt"
    banned_words_path.write_text("")
    return str(banned_words_path)


@pytest.fixture
def sample_bjobs_data():
    """Sample BestJobs data for testing."""
    return [
        {
            "id": 1,
            "slug": "python-developer",
            "title": "Python Developer",
            "companyName": "Tech Corp",
            "active": True,
            "ownApplyUrl": "https://techcorp.com/apply"
        },
        {
            "id": 2,
            "slug": "sales-representative",
            "title": "Sales Representative",
            "companyName": "Sales Inc",
            "active": True,
            "ownApplyUrl": ""
        },
        {
            "id": 3,
            "slug": "software-engineer",
            "title": "Software Engineer",
            "companyName": "Dev Company",
            "active": True,
            "ownApplyUrl": None
        }
    ]


@pytest.fixture
def sample_ejobs_data():
    """Sample eJobs data for testing."""
    return [
        {
            "id": 101,
            "title": "Backend Developer",
            "slug": "backend-developer",
            "creationDate": "2024-01-01",
            "expirationDate": "2024-02-01",
            "externalUrl": "https://company.com/jobs"
        },
        {
            "id": 102,
            "title": "Marketing Manager",
            "slug": "marketing-manager",
            "creationDate": "2024-01-02",
            "expirationDate": "2024-02-02",
            "externalUrl": ""
        },
        {
            "id": 103,
            "title": "DevOps Engineer",
            "slug": "devops-engineer",
            "creationDate": "2024-01-03",
            "expirationDate": "2024-02-03",
            "externalUrl": None
        }
    ]


@pytest.fixture
def sample_bjobs_df(sample_bjobs_data):
    """Sample BestJobs DataFrame for testing."""
    return pd.DataFrame(sample_bjobs_data)


@pytest.fixture
def sample_ejobs_df(sample_ejobs_data):
    """Sample eJobs DataFrame for testing."""
    return pd.DataFrame(sample_ejobs_data)


@pytest.fixture
def timestamp_file(tmp_path):
    """Create a temporary timestamp file."""
    ts_file = tmp_path / "last_run.txt"
    return str(ts_file)


@pytest.fixture
def old_timestamp_file(tmp_path):
    """Create a timestamp file with a date > 24 hours ago."""
    ts_file = tmp_path / "last_run.txt"
    old_time = datetime.now() - timedelta(hours=25)
    ts_file.write_text(old_time.isoformat())
    return str(ts_file)


@pytest.fixture
def recent_timestamp_file(tmp_path):
    """Create a timestamp file with a date < 24 hours ago."""
    ts_file = tmp_path / "last_run.txt"
    recent_time = datetime.now() - timedelta(hours=12)
    ts_file.write_text(recent_time.isoformat())
    return str(ts_file)


@pytest.fixture
def corrupted_timestamp_file(tmp_path):
    """Create a timestamp file with invalid data."""
    ts_file = tmp_path / "last_run.txt"
    ts_file.write_text("invalid-timestamp-data")
    return str(ts_file)
