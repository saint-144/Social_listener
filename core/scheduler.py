import schedule
import time
from core.fetch_job import run_fetch_job


def start_scheduler():

    # run immediately once
    run_fetch_job()

    # schedule heartbeat check every 1 minute
    schedule.every(1).minutes.do(run_fetch_job)

    while True:
        schedule.run_pending()
        time.sleep(30)