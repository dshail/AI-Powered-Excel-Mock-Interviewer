#!/bin/bash

# Excel Mock Interviewer Deployment Script
# This script starts both FastAPI backend and Streamlit frontend

echo "🚀 Starting Excel Mock Interviewer with Gemini AI..."
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Install requirements if needed
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "❗ Please edit .env file and add your GEMINI_API_KEY"
    echo "   Get your API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Start the application
echo "🔥 Starting FastAPI Backend and Streamlit Frontend..."
python main.py