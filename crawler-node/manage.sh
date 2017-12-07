#!/bin/bash
export PYTHONDONTWRITEBYTECODE='1'

source ./local.env

source .venv/bin/activate
cd src
./worker.py $@
cd ..
deactivate
