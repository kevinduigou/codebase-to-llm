#!/bin/bash

# Video Summary Behave Test Runner
# This script demonstrates how to run the behave tests for video summaries

set -e

echo "🧪 Video Summary Behave Test Runner"
echo "===================================="

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! uv run python -c "import behave, requests" 2>/dev/null; then
    echo "Installing dependencies..."
    uv sync --group dev
fi

# Check if server is running (optional - tests will fail gracefully if not)
echo "🔍 Checking if FastAPI server is accessible..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Server is running at http://localhost:8000"
    SERVER_RUNNING=true
else
    echo "⚠️  Server not detected at http://localhost:8000"
    echo "   To run the full tests, start the server with:"
    echo "   uv run uvicorn codebase_to_llm.interface.fastapi.app:app --reload --port 8000"
    SERVER_RUNNING=false
fi

echo ""
echo "🧪 Running behave tests for video summaries..."
echo "=============================================="

if [ "$SERVER_RUNNING" = true ]; then
    echo "Running full integration tests..."
    uv run behave features/video_summary.feature --verbose
else
    echo "Running dry-run (syntax check only)..."
    uv run behave --dry-run features/video_summary.feature
    echo ""
    echo "💡 To run the actual tests:"
    echo "   1. Start the FastAPI server: uv run uvicorn codebase_to_llm.interface.fastapi.app:app --reload --port 8000"
    echo "   2. Run: uv run behave features/video_summary.feature"
fi

echo ""
echo "✨ Test runner completed!"
