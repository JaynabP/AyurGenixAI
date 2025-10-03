#!/bin/bash
set -e

echo "Starting build process..."

# Upgrade pip first
pip install --upgrade pip

# Install requirements with no cache to avoid build issues
pip install --no-cache-dir -r requirements.txt

echo "Build completed successfully!"