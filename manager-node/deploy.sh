#!/bin/bash
# Usage:
# ./deploy.sh crawlers-manager
# where crawlers-manager is an entry from ~/.ssh/config file.

ssh $1 "sudo mkdir -p /opt/mgmt-node; sudo chown -R ubuntu /opt/mgmt-node"
scp -r src/ mgmt-node.env Dockerfile docker-compose.yml $1:/opt/mgmt-node/
