#!/bin/bash
docker run -p 4242:4242 -p 8042:8042 --rm \
  -v $PWD/orthanc-plugins/orthanc.json:/etc/orthanc/orthanc.json:ro \
  -v $PWD/orthanc-plugins/main.py:/usr/local/share/orthanc/plugins/main.py:ro \
  -v $PWD/orthanc-plugins/curapacs_python:/usr/local/share/orthanc/plugins/curapacs_python:ro \
  -v $PWD/_orthanc-peer/libNanoPlugin.so:/usr/local/share/orthanc/plugins/libNanoPlugin.so:ro \
  dumig1/orthanc-python:27-05-rc2
