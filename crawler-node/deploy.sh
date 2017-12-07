#!/bin/bash
ssh $1 "sudo mkdir -p /opt/crawler-node; sudo chown -R ubuntu /opt/crawler-node"
scp -r src/ crawler-node.env Dockerfile docker-compose.yml $1:/opt/crawler-node/
