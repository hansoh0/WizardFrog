#!/bin/bash
# RUN AS DOCKER USER

if [ -a ".env" ]
then
   mkdir -p store

   docker compose build

   docker run -d \
   --name wizardfrog \
   --restart unless-stopped \
   --env-file .env \
   -e ROOT=/home/wizardfrog/app \
   -v "$(pwd)/store:/home/wizardfrog/app" \
   wizardfrog:latest
else
   echo ".env file not set or is not in cwd. Cannot build container."
   exit 1
fi