#!/bin/bash
[ ! -d ./mwl_server ] && { echo "make sure to run this command from the lc2_curapacs directory, exiting"; exit 1; }
docker run -p 4242:4242 -p 8042:8042 --rm \
  -v $PWD/mwl_server/orthanc.json:/etc/orthanc/orthanc.json:ro \
  -v $PWD/mwl_server/app.py:/etc/orthanc/app.py:ro \
  dumig1/orthanc-python:20-05-rc2
