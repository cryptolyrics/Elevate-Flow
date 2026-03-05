#!/bin/bash
# Elevate Flow Sync Script
# Run this to sync local state with canon (origin/main)

echo "=== Elevate Flow Sync ==="

echo "Fetching origin..."
git fetch origin

echo "Resetting to origin/main..."
git reset --hard origin/main

echo "Updating submodules..."
git submodule update --init --recursive

SYNCED_COMMIT=$(git rev-parse HEAD)
echo "SYNCED_COMMIT=$SYNCED_COMMIT"

echo "=== Sync Complete ==="
