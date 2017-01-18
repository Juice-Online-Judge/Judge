FROM python:2.7-alpine

MAINTAINER DanSnow

# Create environment
RUN apk update &&\
    apk add bash gcc libc-dev

# Add judge into container
ADD . /app/
RUN pip install -r /app/requirement.txt

# Create mount point
RUN mkdir -p /share
VOLUME /share
