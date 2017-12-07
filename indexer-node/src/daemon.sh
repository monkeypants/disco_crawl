#!/bin/bash
cd /src/
while true;
do
    ./worker.py  #  >/dev/null 2>/dev/null
    sleep 1
done
