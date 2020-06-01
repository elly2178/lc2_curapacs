import sys
import logging
from orthanc import GetConfiguration
from json import loads

orthanc_config = loads(GetConfiguration())
curapacs_config_section = "Curapacs"

try:
    LOG_FORMAT = orthanc_config.get(curapacs_config_section, {}).get("LOG_FORMAT") or \
                 "%(levelname)s %(asctime)s - %(message)s"
except AttributeError:
    raise AttributeError(f"Config section {curapacs_config_section} is missing.")
LOG_LEVEL = orthanc_config.get(curapacs_config_section, {}).get("LOG_LEVEL") or "INFO"
LOGGING_HANDLER = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[LOGGING_HANDLER], level=logging._nameToLevel[LOG_LEVEL.upper()],
                    format=LOG_FORMAT)
LOGGER = logging.getLogger()

PARENT_NAME = orthanc_config.get(curapacs_config_section, {}).get("PARENT_NAME", "")

if PARENT_NAME:
    PEER_NAME = PARENT_NAME
    PEER_URI = orthanc_config.get("OrthancPeers", {}).get(PEER_NAME, {}).get("Url")
    PEER_HTTP_USER = orthanc_config.get("OrthancPeers", {}).get(PEER_NAME, {}).get("Username") or "orthanc"
    PEER_HTTP_PASSWORD = orthanc_config.get("OrthancPeers", {}).get(PEER_NAME, {}).get("Password") or "orthanc"

HTTP_TIMEOUT = orthanc_config.get(curapacs_config_section, {}).get("HTTP_TIMEOUT") or 5
HTTP_TIMEOUT = int(HTTP_TIMEOUT)
LOCAL_HTTP_PORT = orthanc_config.get("HttpPort") or 8080
LOCAL_HTTP_PORT = int(LOCAL_HTTP_PORT)
LOCAL_WS_PORT = orthanc_config.get(curapacs_config_section, {}).get("WEBSOCKET_PORT", "") or 8081
LOCAL_UNIX_SOCKET_PATH = orthanc_config.get(curapacs_config_section, {}).get("UNIX_SOCKET_PATH", "") or "/tmp/curapacs.sock"
LOCAL_HTTP_USER = list(orthanc_config.get("RegisteredUsers").keys())[0] or "orthanc"
LOCAL_HTTP_PASSWORD = orthanc_config.get("RegisteredUsers", {}).get(LOCAL_HTTP_USER) or "orthanc"
WORKLISTS_DATABASE_DIRECTORY = orthanc_config.get("Worklists", {}).get("Database")
