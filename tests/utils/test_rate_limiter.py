"""Tests for rate limiting functionality."""
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open
from src.pyjobber.utils.rate_limiter import check_last_run, update_timestamp


class TestCheckLastRun:
    """Tests for check_last_run function."""

    def test_check_last_run_no_file(self, timestamp_file):
        """Test that check_last_run returns True when timestamp file doesn't exist."""
        # Ensure file doesn't exist
        if os.path.exists(timestamp_file):
            os.remove(timestamp_file)

        result = check_last_run(timestamp_file)
        assert result is True

    def test_check_last_run_old_timestamp(self, old_timestamp_file):
        """Test that check_last_run returns True when > 24 hours have passed."""
        result = check_last_run(old_timestamp_file)
        assert result is True

    def test_check_last_run_recent_timestamp(self, recent_timestamp_file, capsys):
        """Test that check_last_run returns False when < 24 hours have passed."""
        result = check_last_run(recent_timestamp_file)
        assert result is False

        # Check that informative message was printed
        captured = capsys.readouterr()
        assert "Script last ran" in captured.out
        assert "more hours before next run" in captured.out

    def test_check_last_run_exactly_24_hours(self, tmp_path):
        """Test edge case of exactly 24 hours."""
        ts_file = tmp_path / "exact_24h.txt"
        exactly_24h_ago = datetime.now() - timedelta(hours=24)
        ts_file.write_text(exactly_24h_ago.isoformat())

        result = check_last_run(str(ts_file))
        # Should return True since >= 24 hours
        assert result is True

    def test_check_last_run_just_under_24_hours(self, tmp_path, capsys):
        """Test just under 24 hours (23 hours 59 minutes)."""
        ts_file = tmp_path / "just_under_24h.txt"
        just_under = datetime.now() - timedelta(hours=23, minutes=59)
        ts_file.write_text(just_under.isoformat())

        result = check_last_run(str(ts_file))
        assert result is False

        captured = capsys.readouterr()
        assert "0.0 more hours" in captured.out or "0.1 more hours" in captured.out

    def test_check_last_run_corrupted_file(self, corrupted_timestamp_file):
        """Test that corrupted timestamp file returns True (allows run)."""
        result = check_last_run(corrupted_timestamp_file)
        assert result is True

    def test_check_last_run_empty_file(self, tmp_path):
        """Test handling of empty timestamp file."""
        ts_file = tmp_path / "empty.txt"
        ts_file.write_text("")

        result = check_last_run(str(ts_file))
        # Should return True since file is invalid
        assert result is True

    def test_check_last_run_future_timestamp(self, tmp_path):
        """Test handling of timestamp in the future."""
        ts_file = tmp_path / "future.txt"
        future_time = datetime.now() + timedelta(hours=5)
        ts_file.write_text(future_time.isoformat())

        result = check_last_run(str(ts_file))
        # Should return False since it's "negative" hours since last run
        assert result is False

    @pytest.mark.skipif(os.geteuid() == 0 if hasattr(os, 'geteuid') else False,
                        reason="Cannot test file permissions when running as root")
    def test_check_last_run_file_permission_error(self, tmp_path):
        """Test handling of file permission errors."""
        ts_file = tmp_path / "no_permission.txt"
        ts_file.write_text(datetime.now().isoformat())

        # Make file unreadable (this might not work on all systems)
        if os.name != 'nt':  # Skip on Windows
            os.chmod(str(ts_file), 0o000)

            result = check_last_run(str(ts_file))
            # Should return True when can't read file
            assert result is True

            # Restore permissions for cleanup
            os.chmod(str(ts_file), 0o644)

    def test_check_last_run_multiple_calls_same_file(self, recent_timestamp_file):
        """Test multiple consecutive calls with same file."""
        result1 = check_last_run(recent_timestamp_file)
        result2 = check_last_run(recent_timestamp_file)

        assert result1 == result2
        assert result1 is False

    def test_check_last_run_various_time_differences(self, tmp_path):
        """Test various time differences."""
        test_cases = [
            (timedelta(hours=1), False),
            (timedelta(hours=12), False),
            (timedelta(hours=23), False),
            (timedelta(hours=25), True),
            (timedelta(days=2), True),
            (timedelta(days=7), True),
        ]

        for delta, expected in test_cases:
            ts_file = tmp_path / f"test_{delta.total_seconds()}.txt"
            timestamp = datetime.now() - delta
            ts_file.write_text(timestamp.isoformat())

            result = check_last_run(str(ts_file))
            assert result == expected, f"Failed for delta {delta}"


class TestUpdateTimestamp:
    """Tests for update_timestamp function."""

    def test_update_timestamp_creates_file(self, timestamp_file):
        """Test that update_timestamp creates a new file."""
        # Ensure file doesn't exist
        if os.path.exists(timestamp_file):
            os.remove(timestamp_file)

        update_timestamp(timestamp_file)

        assert os.path.exists(timestamp_file)

    def test_update_timestamp_writes_valid_iso_format(self, timestamp_file):
        """Test that timestamp is written in valid ISO format."""
        update_timestamp(timestamp_file)

        with open(timestamp_file, 'r') as f:
            timestamp_str = f.read().strip()

        # Should be parseable as ISO format
        parsed_time = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_time, datetime)

    def test_update_timestamp_is_recent(self, timestamp_file):
        """Test that timestamp is current (within a few seconds)."""
        before = datetime.now()
        update_timestamp(timestamp_file)
        after = datetime.now()

        with open(timestamp_file, 'r') as f:
            timestamp_str = f.read().strip()

        saved_time = datetime.fromisoformat(timestamp_str)

        # Saved time should be between before and after
        assert before <= saved_time <= after

    def test_update_timestamp_overwrites_existing(self, old_timestamp_file):
        """Test that update_timestamp overwrites existing file."""
        with open(old_timestamp_file, 'r') as f:
            old_content = f.read().strip()

        update_timestamp(old_timestamp_file)

        with open(old_timestamp_file, 'r') as f:
            new_content = f.read().strip()

        # Content should be different
        assert old_content != new_content

        # New timestamp should be more recent
        old_time = datetime.fromisoformat(old_content)
        new_time = datetime.fromisoformat(new_content)
        assert new_time > old_time

    def test_update_timestamp_multiple_calls(self, timestamp_file):
        """Test multiple consecutive update calls."""
        update_timestamp(timestamp_file)
        with open(timestamp_file, 'r') as f:
            first_timestamp = f.read().strip()

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        update_timestamp(timestamp_file)
        with open(timestamp_file, 'r') as f:
            second_timestamp = f.read().strip()

        # Timestamps should be different (second should be newer)
        first_time = datetime.fromisoformat(first_timestamp)
        second_time = datetime.fromisoformat(second_timestamp)
        assert second_time >= first_time

    def test_update_timestamp_with_invalid_path(self, capsys):
        """Test update_timestamp with an invalid directory path."""
        invalid_path = "/nonexistent/directory/timestamp.txt"

        update_timestamp(invalid_path)

        # Should print error message
        captured = capsys.readouterr()
        assert "Error writing timestamp file" in captured.out


class TestRateLimiterIntegration:
    """Integration tests for rate limiter functionality."""

    def test_full_rate_limiter_workflow(self, timestamp_file):
        """Test complete workflow: check, update, check again."""
        # First check - no file exists, should allow
        assert check_last_run(timestamp_file) is True

        # Update timestamp
        update_timestamp(timestamp_file)

        # Check again - file exists with recent timestamp, should not allow
        assert check_last_run(timestamp_file) is False

    def test_rate_limiter_after_24_hours(self, tmp_path):
        """Test that rate limiter allows run after 24 hours."""
        ts_file = tmp_path / "rate_test.txt"

        # Create old timestamp
        old_time = datetime.now() - timedelta(hours=25)
        ts_file.write_text(old_time.isoformat())

        # Should allow run
        assert check_last_run(str(ts_file)) is True

        # Update to current time
        update_timestamp(str(ts_file))

        # Should not allow immediate run
        assert check_last_run(str(ts_file)) is False
