#!/bin/bash
export PYTHONDONTWRITEBYTECODE='1'

source ./local.env

# virtualenv -p /usr/bin/pypy my-pypy-env

source .venv/bin/activate
cd src
./worker.py $@
cd ..
deactivate
