import os
from datetime import datetime, timedelta


def check_last_run(timestamp_file="last_run.txt"):
    """Check if 24 hours have passed since the last run."""
    if not os.path.exists(timestamp_file):
        return True

    try:
        with open(timestamp_file, 'r') as f:
            last_run_str = f.read().strip()

        last_run = datetime.fromisoformat(last_run_str)
        current_time = datetime.now()

        time_diff = current_time - last_run
        if time_diff >= timedelta(days=1):
            return True
        else:
            hours_remaining = 24 - (time_diff.total_seconds() / 3600)
            print(f"Script last ran {time_diff} ago.")
            print(f"Need to wait {hours_remaining:.1f} more hours before next run.")
            return False

    except (ValueError, IOError) as e:
        print(f"Error reading timestamp file: {e}")
        return True


def update_timestamp(timestamp_file="last_run.txt"):
    """Update the timestamp file with the current time."""
    try:
        with open(timestamp_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except IOError as e:
        print(f"Error writing timestamp file: {e}")