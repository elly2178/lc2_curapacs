import logging
import multiprocessing
import sys



LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
LOG_LEVEL = "INFO"
LOGGING_HANDLER = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[LOGGING_HANDLER], level=logging._nameToLevel[LOG_LEVEL.upper()],
                    format=LOG_FORMAT)
LOGGER = logging.getLogger()

def f(number=4):
    LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
    LOG_LEVEL = "INFO"
    LOGGING_HANDLER = logging.StreamHandler(sys.stderr)
    logging.basicConfig(handlers=[LOGGING_HANDLER], level=logging._nameToLevel[LOG_LEVEL.upper()],
                    format=LOG_FORMAT)
    LOGGER = logging.getLogger()
    LOGGER.warning("meow" + str(number))
    print("fubar")
    


if __name__ == '__main__':
    proc = multiprocessing.Process(target=f)
    proc.daemon = True
    proc.start()
        
LOGGER.warning("fuckeroo")