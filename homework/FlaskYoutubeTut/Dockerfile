FROM python:3.8-slim
MAINTAINER BFH Students: dumig1, dresa1
#we jump to the dir /usr/src/app inside the directory
WORKDIR /usr/src/app
#we copy the requirements file from outside the container-image to the inside
COPY MyCode/requirements.txt ./
#this runs the pip command inside the container, so all those dependencies like sqlalchemy and flask will then appear inside your container
RUN pip install --no-cache-dir -r requirements.txt
#this Copy command copies all the files of your program inside the container
#lets put those files in your build environemt (where your Dockerfile is)
COPY MyCode/ .
#when we do "docker run ...", this is the command that will be run by default
CMD [ "python", "./app.py" ]
