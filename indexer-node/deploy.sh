#!/bin/bash
echo "Starting $1"
export TARGET_ROOT=/opt/crawler-node-v2

ssh $1 "sudo mkdir -p ${TARGET_ROOT}; sudo chown -R ubuntu ${TARGET_ROOT}"

# scp -r src/ crawler-node.env Dockerfile docker-compose.yml $1:/opt/crawler-node/

rsync -L --delete --recursive --exclude 'var' \
      --exclude '.venv' --exclude '.git' \
      src crawler-node.env Dockerfile .dockerignore docker-compose.yml src \
      $1:${TARGET_ROOT}

echo "Finished $1"