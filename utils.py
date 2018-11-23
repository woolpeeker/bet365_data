
import logging
from logging.handlers import RotatingFileHandler

def get_logger(name,level=logging.DEBUG, log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(level)
    logger.addHandler(console)

    if log_file is None:
        log_file = 'logs/%s.log' % name
    file_handler = RotatingFileHandler(log_file, mode='w+', maxBytes=50 * 1024 * 1024,
                                       backupCount=10, encoding='UTF-8', delay=0)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    return logger
