from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from includes.fetcher import fetch_rss
from includes.db_utils import push
import logging
import logger_config
import os


# setting the logger
logger_config.set_logger()
logger = logging.getLogger("rss_reader")
# poll interval for scheduler
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL"))
# grace tolerance in case scheduler misses the next firing time
GRACE_TOL = int(os.getenv("GRACE_TOL"))


def worker():
    """Function executed by the scheduler"""
    logger.info("Fetching rss feed...")
    data = fetch_rss()
    push(data)
    logger.info("Pushed to db successfully.")


def main():
    """Function to set-up the scheduler"""
    print("RSS Reader started. Press CTRL+C to stop.")
    scheduler = BlockingScheduler()
    scheduler.add_job(worker, 'interval', seconds=POLL_INTERVAL,
                      next_run_time=datetime.now(), misfire_grace_time=GRACE_TOL)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nRSS Reader stopped by user.")


if __name__ == "__main__":
    main()
