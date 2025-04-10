#!/bin/bash

docker compose -f docker-compose.renesas.yaml up -d --build

docker image prune -f
