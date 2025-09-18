#!/usr/bin/env bash
# build.sh - Build script for Render

# Exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo "Build completed successfully!"