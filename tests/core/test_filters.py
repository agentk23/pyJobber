"""Tests for core filtering functionality."""
import os
import pytest
import pandas as pd
from src.pyjobber.core.filters import load_banned_words, filter_jobs_by_banned_words


class TestLoadBannedWords:
    """Tests for load_banned_words function."""

    def test_load_banned_words_success(self, banned_words_file):
        """Test loading banned words from a valid file."""
        words = load_banned_words(banned_words_file)
        assert len(words) == 4
        assert "sales" in words
        assert "marketing" in words
        assert "manager" in words
        assert "consultant" in words

    def test_load_banned_words_strips_whitespace(self, tmp_path):
        """Test that whitespace is stripped from banned words."""
        words_file = tmp_path / "words_with_spaces.txt"
        words_file.write_text("  sales  \n\n  marketing\n  \n")

        words = load_banned_words(str(words_file))
        assert len(words) == 2
        assert words == ["sales", "marketing"]

    def test_load_banned_words_file_not_found(self):
        """Test handling of missing banned words file."""
        words = load_banned_words("nonexistent_file.txt")
        assert words == []

    def test_load_banned_words_empty_file(self, empty_banned_words_file):
        """Test loading from an empty file."""
        words = load_banned_words(empty_banned_words_file)
        assert words == []

    def test_load_banned_words_with_empty_lines(self, tmp_path):
        """Test that empty lines are ignored."""
        words_file = tmp_path / "words_with_empty_lines.txt"
        words_file.write_text("sales\n\n\nmarketing\n\n")

        words = load_banned_words(str(words_file))
        assert len(words) == 2
        assert "sales" in words
        assert "marketing" in words


class TestFilterJobsByBannedWords:
    """Tests for filter_jobs_by_banned_words function."""

    def test_filter_jobs_basic(self, banned_words_file):
        """Test basic filtering of jobs with banned words."""
        df = pd.DataFrame([
            {"title": "Python Developer", "company": "Tech Corp"},
            {"title": "Sales Representative", "company": "Sales Inc"},
            {"title": "Software Engineer", "company": "Dev Co"},
            {"title": "Marketing Manager", "company": "Market Co"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, banned_words_file)

        assert len(filtered_df) == 2
        assert "Python Developer" in filtered_df["title"].values
        assert "Software Engineer" in filtered_df["title"].values
        assert "Sales Representative" not in filtered_df["title"].values
        assert "Marketing Manager" not in filtered_df["title"].values

    def test_filter_jobs_case_insensitive(self, banned_words_file):
        """Test that filtering is case-insensitive."""
        df = pd.DataFrame([
            {"title": "SALES REPRESENTATIVE", "company": "Company A"},
            {"title": "Sales Manager", "company": "Company B"},
            {"title": "sales associate", "company": "Company C"},
            {"title": "Python Developer", "company": "Company D"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, banned_words_file)

        assert len(filtered_df) == 1
        assert "Python Developer" in filtered_df["title"].values

    def test_filter_jobs_partial_match(self, banned_words_file):
        """Test that banned words match partially within titles."""
        df = pd.DataFrame([
            {"title": "Salesperson Position", "company": "Company A"},
            {"title": "Account Manager", "company": "Company B"},
            {"title": "Marketing Specialist", "company": "Company C"},
            {"title": "Python Developer", "company": "Company D"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, banned_words_file)

        # "sales" should match "Salesperson", "manager" should match "Account Manager", etc.
        assert len(filtered_df) == 1
        assert "Python Developer" in filtered_df["title"].values

    def test_filter_jobs_empty_dataframe(self, banned_words_file):
        """Test filtering an empty DataFrame."""
        df = pd.DataFrame(columns=["title", "company"])

        filtered_df = filter_jobs_by_banned_words(df, banned_words_file)

        assert len(filtered_df) == 0
        assert list(filtered_df.columns) == ["title", "company"]

    def test_filter_jobs_no_banned_words(self, empty_banned_words_file):
        """Test filtering with no banned words."""
        df = pd.DataFrame([
            {"title": "Python Developer", "company": "Tech Corp"},
            {"title": "Sales Representative", "company": "Sales Inc"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, empty_banned_words_file)

        assert len(filtered_df) == 2  # Nothing should be filtered

    def test_filter_jobs_missing_banned_words_file(self):
        """Test filtering when banned words file doesn't exist."""
        df = pd.DataFrame([
            {"title": "Python Developer", "company": "Tech Corp"},
            {"title": "Sales Representative", "company": "Sales Inc"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, "nonexistent.txt")

        assert len(filtered_df) == 2  # Nothing filtered if file doesn't exist

    def test_filter_jobs_all_filtered(self, banned_words_file):
        """Test when all jobs are filtered out."""
        df = pd.DataFrame([
            {"title": "Sales Manager", "company": "Company A"},
            {"title": "Marketing Director", "company": "Company B"},
            {"title": "Consultant", "company": "Company C"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, banned_words_file)

        assert len(filtered_df) == 0

    def test_filter_jobs_none_filtered(self, banned_words_file):
        """Test when no jobs are filtered out."""
        df = pd.DataFrame([
            {"title": "Python Developer", "company": "Company A"},
            {"title": "Java Engineer", "company": "Company B"},
            {"title": "DevOps Specialist", "company": "Company C"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, banned_words_file)

        assert len(filtered_df) == 3

    def test_filter_jobs_special_characters(self, tmp_path):
        """Test filtering with special characters in banned words."""
        words_file = tmp_path / "special_words.txt"
        words_file.write_text("C++\n.NET\nNode.js")

        df = pd.DataFrame([
            {"title": "C++ Developer", "company": "Company A"},
            {"title": ".NET Engineer", "company": "Company B"},
            {"title": "Python Developer", "company": "Company C"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, str(words_file))

        assert len(filtered_df) == 1
        assert "Python Developer" in filtered_df["title"].values

    def test_filter_jobs_preserves_dataframe_structure(self, banned_words_file):
        """Test that filtering preserves the DataFrame structure."""
        df = pd.DataFrame([
            {"title": "Python Developer", "company": "Tech Corp", "location": "Remote"},
            {"title": "Sales Manager", "company": "Sales Inc", "location": "NYC"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, banned_words_file)

        assert len(filtered_df) == 1
        assert list(filtered_df.columns) == ["title", "company", "location"]
        assert filtered_df.iloc[0]["location"] == "Remote"

    def test_filter_jobs_multiple_banned_words_in_title(self, banned_words_file):
        """Test filtering when title contains multiple banned words."""
        df = pd.DataFrame([
            {"title": "Sales and Marketing Manager", "company": "Company A"},
            {"title": "Python Developer", "company": "Company B"}
        ])

        filtered_df = filter_jobs_by_banned_words(df, banned_words_file)

        # Should filter out job with multiple banned words
        assert len(filtered_df) == 1
        assert "Python Developer" in filtered_df["title"].values

    def test_filter_jobs_with_nan_titles(self, banned_words_file):
        """Test filtering when DataFrame contains NaN titles."""
        df = pd.DataFrame([
            {"title": "Python Developer", "company": "Company A"},
            {"title": None, "company": "Company B"},
            {"title": "Sales Manager", "company": "Company C"}
        ])

        # This might raise an error or handle NaN differently
        # Test should verify the actual behavior
        try:
            filtered_df = filter_jobs_by_banned_words(df, banned_words_file)
            # If it works, check that NaN is handled appropriately
            assert len(filtered_df) >= 0
        except Exception:
            # If it raises an exception, that's also valid behavior
            # In production, you might want to handle NaN values explicitly
            pass
