#!/bin/bash

# Test Market Data Integration
# This script runs both the integration example and the unit tests

echo "=== Crypto Market Making Market Data Integration Tests ==="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the unit tests
echo "Running unit tests..."
python tests/test_market_data_integration.py
TEST_EXIT_CODE=$?

# Run the integration example if tests succeeded
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Running integration example..."
    python scripts/integration_example.py
    EXAMPLE_EXIT_CODE=$?
else
    echo "Tests failed. Skipping integration example."
    EXAMPLE_EXIT_CODE=1
fi

# Print summary
echo ""
echo "=== Test Summary ==="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Unit tests: PASSED"
else
    echo "❌ Unit tests: FAILED"
fi

if [ $EXAMPLE_EXIT_CODE -eq 0 ]; then
    echo "✅ Integration example: PASSED"
else
    echo "❌ Integration example: FAILED"
fi

# Return overall status
if [ $TEST_EXIT_CODE -eq 0 ] && [ $EXAMPLE_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    exit 0
else
    echo ""
    echo "❌ There were test failures."
    exit 1
fi 