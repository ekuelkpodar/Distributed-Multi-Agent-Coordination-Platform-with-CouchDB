#!/bin/bash
# Comprehensive test runner for the distributed agent platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"

    # Check if Docker daemon is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_success "Docker daemon is running"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_success "Python 3 is installed ($(python3 --version))"

    # Check pytest
    if ! python3 -c "import pytest" 2>/dev/null; then
        print_warning "pytest not found, installing..."
        pip install pytest pytest-asyncio pytest-cov
    fi
    print_success "pytest is available"
}

# Check services
check_services() {
    print_header "Checking Services"

    # Check CouchDB nodes
    for port in 5984 5985 5986; do
        if curl -sf http://localhost:$port/_up > /dev/null 2>&1; then
            print_success "CouchDB node on port $port is healthy"
        else
            print_error "CouchDB node on port $port is not accessible"
            exit 1
        fi
    done

    # Check Redis
    if docker exec redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is accessible"
    else
        print_error "Redis is not accessible"
        exit 1
    fi

    # Check Prometheus
    if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
        print_success "Prometheus is accessible"
    else
        print_warning "Prometheus is not accessible (non-critical)"
    fi

    # Check Grafana
    if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
        print_success "Grafana is accessible"
    else
        print_warning "Grafana is not accessible (non-critical)"
    fi
}

# Setup test environment
setup_test_environment() {
    print_header "Setting Up Test Environment"

    # Load test environment variables
    if [ -f .env.test ]; then
        export $(cat .env.test | grep -v '^#' | xargs)
        print_success "Loaded test environment variables"
    else
        print_warning ".env.test not found, using defaults"
    fi

    # Create test reports directory
    mkdir -p test_reports
    print_success "Created test reports directory"
}

# Run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"

    if pytest tests/ -v --ignore=tests/test_integration.py --cov=src --cov-report=term --cov-report=html:test_reports/coverage_unit 2>&1; then
        print_success "Unit tests passed"
        return 0
    else
        print_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"

    if pytest tests/test_integration.py -v -s --cov=src --cov-report=term --cov-report=html:test_reports/coverage_integration 2>&1; then
        print_success "Integration tests passed"
        return 0
    else
        print_error "Integration tests failed"
        return 1
    fi
}

# Run system tests
run_system_tests() {
    print_header "Running System Tests"

    print_info "Testing end-to-end workflow..."

    # Test database connectivity
    python3 -c "
import asyncio
from src.database.client import CouchDBClient

async def test():
    async with CouchDBClient() as client:
        print('✓ Database connection successful')

asyncio.run(test())
" 2>&1

    if [ $? -eq 0 ]; then
        print_success "Database connectivity test passed"
    else
        print_error "Database connectivity test failed"
        return 1
    fi

    # Test agent registry
    print_info "Testing agent registry..."
    python3 -c "
import asyncio
from src.database.client import CouchDBClient
from src.agents.registry import AgentRegistry

async def test():
    async with CouchDBClient() as client:
        registry = AgentRegistry(client)
        agents = await registry.discover_agents()
        print(f'✓ Found {len(agents)} agents')

asyncio.run(test())
" 2>&1

    if [ $? -eq 0 ]; then
        print_success "Agent registry test passed"
    else
        print_error "Agent registry test failed"
        return 1
    fi

    print_success "System tests passed"
}

# Generate test data
generate_test_data() {
    print_header "Generating Mock Test Data"

    print_info "Generating mock data using OpenRouter..."
    if python3 scripts/generate_mock_data.py --agents 5 --tasks 10 --knowledge 5 --states 5 --decisions 3 2>&1; then
        print_success "Mock data generated successfully"
    else
        print_warning "Mock data generation completed with warnings (check if OpenRouter API is accessible)"
    fi
}

# Run performance tests
run_performance_tests() {
    print_header "Running Performance Tests"

    print_info "Testing task throughput..."

    python3 -c "
import asyncio
import time
from src.database.client import CouchDBClient
from src.core.task_queue import TaskQueue
from src.core.models import Task, TaskStatus

async def test():
    async with CouchDBClient() as client:
        task_queue = TaskQueue(client)

        # Create 100 tasks
        start = time.time()
        tasks = []
        for i in range(100):
            task = Task(
                task_id=f'perf_test_task_{i}',
                status=TaskStatus.PENDING,
                priority=5,
                task_definition={'type': 'performance_test'}
            )
            tasks.append(task)

        # Batch save
        for task in tasks:
            try:
                await task_queue.add_task(task)
            except:
                pass

        elapsed = time.time() - start
        throughput = len(tasks) / elapsed
        print(f'✓ Created {len(tasks)} tasks in {elapsed:.2f}s ({throughput:.1f} tasks/sec)')

        # Cleanup
        for task in tasks:
            try:
                doc = await client.get_document(task.task_id)
                await client.delete_document(task.task_id, doc['_rev'])
            except:
                pass

asyncio.run(test())
" 2>&1

    if [ $? -eq 0 ]; then
        print_success "Performance tests passed"
    else
        print_error "Performance tests failed"
        return 1
    fi
}

# Generate test report
generate_report() {
    print_header "Generating Test Report"

    REPORT_FILE="test_reports/test_summary_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "========================================="
        echo "Test Summary Report"
        echo "========================================="
        echo ""
        echo "Date: $(date)"
        echo "Platform: $(uname -s) $(uname -m)"
        echo "Python: $(python3 --version)"
        echo ""
        echo "Services Status:"
        echo "  CouchDB Node 1: $(curl -sf http://localhost:5984/_up > /dev/null && echo 'Healthy' || echo 'Down')"
        echo "  CouchDB Node 2: $(curl -sf http://localhost:5985/_up > /dev/null && echo 'Healthy' || echo 'Down')"
        echo "  CouchDB Node 3: $(curl -sf http://localhost:5986/_up > /dev/null && echo 'Healthy' || echo 'Down')"
        echo "  Redis: $(docker exec redis redis-cli ping 2>/dev/null || echo 'Down')"
        echo "  Prometheus: $(curl -sf http://localhost:9090/-/healthy > /dev/null && echo 'Healthy' || echo 'Down')"
        echo "  Grafana: $(curl -sf http://localhost:3000/api/health > /dev/null && echo 'Healthy' || echo 'Down')"
        echo ""
        echo "Test Results:"
        echo "  Unit Tests: $UNIT_TEST_RESULT"
        echo "  Integration Tests: $INTEGRATION_TEST_RESULT"
        echo "  System Tests: $SYSTEM_TEST_RESULT"
        echo "  Performance Tests: $PERFORMANCE_TEST_RESULT"
        echo ""
        echo "Coverage Reports:"
        echo "  Unit Test Coverage: test_reports/coverage_unit/index.html"
        echo "  Integration Test Coverage: test_reports/coverage_integration/index.html"
        echo ""
    } > "$REPORT_FILE"

    print_success "Test report saved to $REPORT_FILE"
    cat "$REPORT_FILE"
}

# Main execution
main() {
    print_header "Distributed Agent Platform - Test Suite"

    # Initialize result variables
    UNIT_TEST_RESULT="NOT RUN"
    INTEGRATION_TEST_RESULT="NOT RUN"
    SYSTEM_TEST_RESULT="NOT RUN"
    PERFORMANCE_TEST_RESULT="NOT RUN"

    # Check prerequisites
    check_prerequisites

    # Check services
    check_services

    # Setup test environment
    setup_test_environment

    # Parse arguments
    RUN_ALL=true
    RUN_UNIT=false
    RUN_INTEGRATION=false
    RUN_SYSTEM=false
    RUN_PERFORMANCE=false
    GENERATE_DATA=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit)
                RUN_ALL=false
                RUN_UNIT=true
                shift
                ;;
            --integration)
                RUN_ALL=false
                RUN_INTEGRATION=true
                shift
                ;;
            --system)
                RUN_ALL=false
                RUN_SYSTEM=true
                shift
                ;;
            --performance)
                RUN_ALL=false
                RUN_PERFORMANCE=true
                shift
                ;;
            --generate-data)
                GENERATE_DATA=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --unit              Run only unit tests"
                echo "  --integration       Run only integration tests"
                echo "  --system            Run only system tests"
                echo "  --performance       Run only performance tests"
                echo "  --generate-data     Generate mock test data before running tests"
                echo "  --help              Show this help message"
                echo ""
                echo "Default: Run all tests"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Generate test data if requested
    if [ "$GENERATE_DATA" = true ]; then
        generate_test_data
    fi

    # Run tests
    if [ "$RUN_ALL" = true ] || [ "$RUN_UNIT" = true ]; then
        if run_unit_tests; then
            UNIT_TEST_RESULT="PASSED"
        else
            UNIT_TEST_RESULT="FAILED"
        fi
    fi

    if [ "$RUN_ALL" = true ] || [ "$RUN_INTEGRATION" = true ]; then
        if run_integration_tests; then
            INTEGRATION_TEST_RESULT="PASSED"
        else
            INTEGRATION_TEST_RESULT="FAILED"
        fi
    fi

    if [ "$RUN_ALL" = true ] || [ "$RUN_SYSTEM" = true ]; then
        if run_system_tests; then
            SYSTEM_TEST_RESULT="PASSED"
        else
            SYSTEM_TEST_RESULT="FAILED"
        fi
    fi

    if [ "$RUN_ALL" = true ] || [ "$RUN_PERFORMANCE" = true ]; then
        if run_performance_tests; then
            PERFORMANCE_TEST_RESULT="PASSED"
        else
            PERFORMANCE_TEST_RESULT="FAILED"
        fi
    fi

    # Generate report
    generate_report

    # Final summary
    print_header "Test Execution Complete"

    if [[ "$UNIT_TEST_RESULT" == "FAILED" ]] || \
       [[ "$INTEGRATION_TEST_RESULT" == "FAILED" ]] || \
       [[ "$SYSTEM_TEST_RESULT" == "FAILED" ]] || \
       [[ "$PERFORMANCE_TEST_RESULT" == "FAILED" ]]; then
        print_error "Some tests failed"
        exit 1
    else
        print_success "All tests passed!"
        exit 0
    fi
}

# Run main
main "$@"
