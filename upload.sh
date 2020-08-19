#!/usr/bin/env bash

if [ -n "$1" ]
then
docker build -t usrnm242/flaskbot:$1 .
docker push usrnm242/flaskbot:$1
else
docker build -t usrnm242/flaskbot:latest .
docker push usrnm242/flaskbot:latest
fi
