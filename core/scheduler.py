import schedule
import time
from core.config import FETCH_INTERVAL_MINUTES
from core.fetch_job import run_fetch_job


def start_scheduler():

    # run immediately once
    run_fetch_job()

    # schedule future runs
    schedule.every(FETCH_INTERVAL_MINUTES).minutes.do(run_fetch_job)

    while True:
        schedule.run_pending()
        time.sleep(30)