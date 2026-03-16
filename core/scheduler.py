import time
from core.fetch_job import run_fetch_job

HEARTBEAT_INTERVAL_SECONDS = 30


def start_scheduler():
    # Run immediately on start (first run for all platforms)
    run_fetch_job()

    # Then wake every 30 seconds to check if any platform is due
    while True:
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)
        run_fetch_job()