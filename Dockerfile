# all Dockerfiles have a FROM
FROM node:6-alpine
# expose port 3 000
EXPOSE 3000
# alpine needs to use a package manager to install tini -> use a rum command
RUN apk add --update tini
RUN mkdir -p /usr/src/app
# copy it in a single file -> better use WORKDIR
WORKDIR /usr/src/app
COPY files/package.json package.json

# it needs to run a npm install
RUN npm install && npm cache clean
# copy all files from current directory
COPY files/ .
# start a container with command tini -- node ./bin/www
CMD ["tini", "--", "./bin/www"]
