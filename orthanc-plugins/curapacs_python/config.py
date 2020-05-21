import os
import sys
import logging

def set_config_value(config_key):
    """
    Set defaults first
    Use orthanc.GetConfiguration() second
    Use environment vars third
    """

LOG_FORMAT = os.environ.get("CURAPACS_LOG_FORMAT", "%(levelname)s %(asctime)s - %(message)s")
LOG_LEVEL = os.environ.get("CURAPACS_LOG_LEVEL", "DEBUG")

LOGGING_HANDLER = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[LOGGING_HANDLER], level=logging._nameToLevel[LOG_LEVEL.upper()], format=LOG_FORMAT)
LOGGER = logging.getLogger()

PEER_NAME = "c0100-orthanc"
PEER_DOMAIN = "curapacs.ch"
LOCAL_HTTP_PORT = 8042
ORTHANC_URI = "http://c0100-orthanc.curapacs.ch"
HTTP_TIMEOUT = 5
HTTP_USER = "orthanc"
HTTP_PASSWORD = "orthanc"
