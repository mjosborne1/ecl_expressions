#!/usr/bin/env bash
# Build script for render.com deployment

set -o errexit  # Exit on error

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs

echo "Build completed successfully!"