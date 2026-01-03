#!/bin/bash
# Start the admin dashboard

set -e

echo "=========================================="
echo "Starting Admin Dashboard"
echo "=========================================="
echo ""

# Check if services are running
echo "Checking services..."
if ! curl -sf http://localhost:5984/_up > /dev/null 2>&1; then
    echo "❌ CouchDB is not running. Please start services first:"
    echo "   make start"
    exit 1
fi
echo "✓ CouchDB is running"

# Start the API server
echo ""
echo "Starting admin API server..."
echo "Dashboard will be available at: http://localhost:8000"
echo ""

cd "$(dirname "$0")/.."
PYTHONPATH=. python3 src/api/admin_api.py
