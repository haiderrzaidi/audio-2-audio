#!/bin/bash

apt-get update
apt-get install -y make automake gcc g++ subversion python3-dev
pre-commit install