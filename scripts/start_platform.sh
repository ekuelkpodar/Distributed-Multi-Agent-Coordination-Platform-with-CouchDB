#!/bin/bash
# Start the distributed agent platform

set -e

echo "=========================================="
echo "Starting Distributed Agent Platform"
echo "=========================================="
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start CouchDB cluster
echo "1. Starting CouchDB cluster..."
docker-compose up -d

echo "   Waiting for CouchDB nodes to be ready..."
sleep 10

# Wait for all nodes to be healthy
for port in 5984 5985 5986; do
    echo "   Checking CouchDB node on port $port..."
    until curl -sf http://localhost:$port/_up > /dev/null 2>&1; do
        echo "   Waiting for node on port $port..."
        sleep 2
    done
    echo "   ✓ Node on port $port is ready"
done

echo

# Initialize database
echo "2. Initializing database..."
python3 scripts/init_database.py

echo
echo "=========================================="
echo "Platform started successfully!"
echo "=========================================="
echo
echo "Services:"
echo "  - CouchDB Node 1: http://localhost:5984"
echo "  - CouchDB Node 2: http://localhost:5985"
echo "  - CouchDB Node 3: http://localhost:5986"
echo "  - Redis: localhost:6379"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo
echo "Credentials:"
echo "  - CouchDB: admin / password"
echo "  - Grafana: admin / admin"
echo
echo "Next steps:"
echo "  1. Copy .env.example to .env and configure"
echo "  2. Run example: python3 examples/distributed_research.py"
echo "  3. View CouchDB admin: http://localhost:5984/_utils"
echo
