#!/usr/bin/env bash
set -eu
python3 "$(dirname "$0")/../fixture.py" install
python3 "$(dirname "$0")/../fixture.py" repo acme-api
