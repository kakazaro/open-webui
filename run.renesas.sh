#!/bin/bash

image_name="kakazaro/open-webui:latest"

git pull

docker build -f Dockerfile.renesas -t "$image_name" .
docker push "$image_name"

docker compose -f docker-compose.renesas.yaml up -d

docker image prune -f
