#!/bin/bash -e

# execute the script from the tool path
cd $(realpath $(dirname $0))

# Create virtual environment if needed
if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate

# Upgrade pip
if ! command -v pip &> /dev/null; then
    python3 -m ensurepip --upgrade
fi

# Install dependencies
pip install -r requirements.txt

# Run the script
python3 start.py
