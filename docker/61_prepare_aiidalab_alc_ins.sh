#!/bin/bash

set -euo pipefail

APP_DIR="${HOME}/apps/aiidalab-alc-ins"

echo "Installing the AiiDAlab ALC INS application"
cd "${APP_DIR}"
pip install --editable . --no-cache-dir --no-user --quiet