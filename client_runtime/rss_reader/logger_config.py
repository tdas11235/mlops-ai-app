import logging
import os
import sys


def set_logger():
    log_dir = "/app/logs"
    log_file = os.path.join(log_dir, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler() if sys.stdout.encoding.lower(
            ) == 'utf-8' else logging.StreamHandler(sys.stdout, encoding='utf-8'),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)
