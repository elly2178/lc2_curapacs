#!/bin/bash
docker run -p 4242:4242 -p 8042:8042 --rm \
  -v $PWD/orthanc-peer/orthanc.json:/etc/orthanc/orthanc.json:ro \
  -v $PWD/orthanc-peer/sample.py:/etc/orthanc/sample.py:ro \
  -v $PWD/orthanc-peer/libNanoPlugin.so:/usr/local/share/orthanc/plugins/libNanoPlugin.so:ro \
  dumig1/orthanc-python:20-05-rc2
