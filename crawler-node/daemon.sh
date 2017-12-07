#!/bin/bash
export PYTHONDONTWRITEBYTECODE='1'

source ./local.env

source .venv/bin/activate
cd src
while true;
do
    ./worker.py
done
cd ..
deactivate
