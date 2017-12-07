#!/bin/bash
#
ssh $1 "sudo apt update && sudo apt install htop docker.io python-pip -y && sudo pip install --upgrade pip wheel && sudo pip install docker-compose"
