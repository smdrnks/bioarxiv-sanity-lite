#!/bin/bash

python bioarxiv_daemon.py

if [ $? -eq 0 ]; then
    echo "New papers detected! Running compute.py"
    python compute.py
else
    echo "No new papers were added, skipping feature computation"
fi