import os
import sys
import logging
from orthanc import GetConfiguration
from json import loads

def get_config_value(config_key: str, orthanc_config_section: dict, 
                     orthanc_env_prefix="CURAPACS", default=None):
    """
    Use environment vars as first priority
    Use orthanc config file second
    Use defaults third
    """
    cfg = orthanc_config_section
    return os.environ.get(orthanc_env_prefix + "_" + config_key) or cfg.get(config_key) or default

orthanc_config = loads(GetConfiguration())
orthanc_config_section = "CURAPACS"

LOG_FORMAT = get_config_value("LOG_FORMAT", orthanc_config.get(orthanc_config_section),
                              default="%(levelname)s %(asctime)s - %(message)s")
LOG_LEVEL = get_config_value("LOG_LEVEL", orthanc_config.get(orthanc_config_section),
                             default="DEBUG")
LOGGING_HANDLER = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[LOGGING_HANDLER], level=logging._nameToLevel[LOG_LEVEL.upper()],
                    format=LOG_FORMAT)
LOGGER = logging.getLogger()


PARENT_NAME = orthanc_config.get("CURAPACS").get("PARENT_NAME")
if PARENT_NAME:
    PEER_NAME = PARENT_NAME
    PEER_URI = orthanc_config.get("OrthancPeers").get(PEER_NAME).get("Url")
    PEER_HTTP_USER = orthanc_config.get("OrthancPeers").get(PEER_NAME).get("Username") or "orthanc"
    PEER_HTTP_PASSWORD = orthanc_config.get("OrthancPeers").get(PEER_NAME).get("Password") or "orthanc"

HTTP_TIMEOUT = int(get_config_value("HTTP_TIMEOUT", orthanc_config.get(orthanc_config_section),
                                    default=5))
LOCAL_HTTP_PORT = int(orthanc_config.get("HttpPort"))
LOCAL_HTTP_USER = list(orthanc_config.get("RegisteredUsers").keys())[0] or "orthanc"
LOCAL_HTTP_PASSWORD = orthanc_config.get("RegisteredUsers").get(LOCAL_HTTP_USER) or "orthanc"
WORKLISTS_DATABASE_DIRECTORY = orthanc_config.get("Worklists").get("Database")
