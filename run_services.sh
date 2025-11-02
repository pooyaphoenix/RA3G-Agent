#!/bin/bash

# Script to run both FastAPI and Streamlit services
# Make sure you're in the project directory

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

echo "=================================="
echo "Starting RAG Gateway Services"
echo "=================================="
echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo "Starting Streamlit dashboard on http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill 0
    exit
}

trap cleanup INT TERM

# Start FastAPI in background
uvicorn app.main:app --reload --port 8000 &
FASTAPI_PID=$!

# Wait a moment for FastAPI to start
sleep 2

# Start Streamlit in background
streamlit run viewer.py &
STREAMLIT_PID=$!

# Wait for both processes
wait

