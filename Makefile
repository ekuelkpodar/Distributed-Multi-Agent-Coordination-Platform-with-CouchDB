.PHONY: help install start stop restart clean test example docs

help:
	@echo "Distributed Multi-Agent Coordination Platform"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make start      - Start the platform (Docker + Database)"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make clean      - Stop services and remove volumes"
	@echo "  make test       - Run tests"
	@echo "  make example    - Run distributed research example"
	@echo "  make logs       - View Docker logs"
	@echo "  make shell      - Open CouchDB shell"

install:
	pip install -r requirements.txt

start:
	@echo "Starting platform..."
	./scripts/start_platform.sh

stop:
	@echo "Stopping services..."
	docker-compose down

restart: stop start

clean:
	@echo "Cleaning up (removes all data)..."
	docker-compose down -v

test:
	@echo "Running tests..."
	pytest -v

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term tests/

example:
	@echo "Running distributed research example..."
	python3 examples/distributed_research.py

logs:
	docker-compose logs -f

logs-couchdb:
	docker-compose logs -f couchdb-node1 couchdb-node2 couchdb-node3

shell:
	@echo "Opening CouchDB shell (node 1)..."
	@echo "URL: http://localhost:5984/_utils"
	open http://localhost:5984/_utils || xdg-open http://localhost:5984/_utils || echo "Visit http://localhost:5984/_utils"

status:
	@echo "Service Status:"
	@docker-compose ps
	@echo ""
	@echo "CouchDB Health:"
	@curl -sf http://localhost:5984/_up && echo "✓ Node 1: Healthy" || echo "✗ Node 1: Down"
	@curl -sf http://localhost:5985/_up && echo "✓ Node 2: Healthy" || echo "✗ Node 2: Down"
	@curl -sf http://localhost:5986/_up && echo "✓ Node 3: Healthy" || echo "✗ Node 3: Down"

init-db:
	@echo "Initializing database..."
	python3 scripts/init_database.py

.DEFAULT_GOAL := help
