#!/bin/bash
docker run -p 4242:4242 -p 8080:8080 --rm \
  -v $PWD/orthanc-plugins/orthanc.json:/etc/orthanc/orthanc.json:ro \
  -v $PWD/orthanc-plugins/main.py:/usr/share/orthanc/curapacs/main.py:ro \
  -v $PWD/orthanc-plugins/curapacs_python:/usr/share/orthanc/curapacs/curapacs_python:ro \
  -v $PWD/_orthanc-peer/libNanoPlugin.so:/usr/share/orthanc/plugins/libNanoPlugin.so:ro \
  -e "VERBOSE_STARTUP=true" \
  dumig1/orthanc-python:27-05-rc2

exit

  -e "ORTHANC__CURAPACS='{\"PARENT_NAME\": \"c0100\"}'" \
  -e "ORTHANC__PYTHON_SCRIPT=/usr/local/share/orthanc/plugins/main.py" \
  -e "PYTHON_PLUGIN_ENABLED=true" \
  -e "ORTHANC__REGISTERED_USERS=\"{'orthanc': 'orthanc'}\"" \
  -e "HTTP_PORT=8080" \
  -e "ORTHANC__ORTHANC_PEERS='{\"orthanc-peer\": [\"http://c0100-orthanc.curapacs.ch\"]}'" \
