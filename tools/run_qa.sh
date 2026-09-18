#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-}:src"
python -m compileall -q src tools tests
python tools/qa_implementation.py
python tools/qa_v02.py
python tools/qa_v04.py
python -m pytest --cov=src/gwr --cov-report=term --cov-report=xml:evidence/v0.4/coverage.xml
