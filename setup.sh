#!/bin/bash

python -m venv .cedar_venv
source .cedar_venv/bin/activate
pip install -e ".[dev,docs,cedar-detect]"

