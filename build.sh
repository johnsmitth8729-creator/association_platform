#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create upload directories if they don't exist
mkdir -p uploads
mkdir -p exports

# Run database migrations
flask db upgrade
