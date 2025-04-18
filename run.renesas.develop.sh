#!/bin/bash

docker compose -f docker-compose.renesas.develop.yaml up -d --build

docker image prune -f
