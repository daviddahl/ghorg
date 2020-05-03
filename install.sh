#! /usr/bin/env bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "Checking for ghorg python virtualenv..."

DIRECTORY=${DIR}/.env

if [ -d "$DIRECTORY" ]; then
    echo "python virtualenv exists"
    python3 -m venv ${DIRECTORY}
fi

if [ ! -d "$DIRECTORY" ]; then
    echo "creating python virtualenv"
    python3 -m venv ${DIRECTORY}
fi

echo "Activating virtualenv"
source ${DIR}/.env/bin/activate

echo "Installing dependencies..."
pip install -r ${DIR}/requirements.txt

echo "All set, you can run ghorg by activating the virtualenv like so:"
echo "source $DIR/.env/bin/activate"
echo "Once the virtualenv is active, run:"
echo "./ghorg -h"
