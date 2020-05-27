FROM osimis/orthanc

RUN 	apt-get upgrade && \
	apt-get update && \
	apt-get install -y python3-pip && \
	pip3 install pydicom requests websockets asyncio && \
	apt-get remove -y python3-pip && \
	apt autoremove -y

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD  ["/tmp/orthanc.json"]

