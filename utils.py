
import logging


def get_logger(name,level=logging.DEBUG):
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    file_handler = logging.FileHandler(name + ".log", "w", encoding="UTF-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(level)

    logger=logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
