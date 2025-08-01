#!/bin/bash
# Quick deployment script for Unix/Linux systems

set -e  # Exit on any error

echo "🚀 Energy Certificate Database Deployment"
echo "========================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if required environment variable is set
if [ -z "$DATABASE_CONNECTION_STRING" ]; then
    echo "❌ DATABASE_CONNECTION_STRING environment variable is not set"
    echo "   Example: export DATABASE_CONNECTION_STRING='Driver={ODBC Driver 17 for SQL Server};Server=server;Database=db;UID=user;PWD=pass'"
    exit 1
fi

# Navigate to database directory
cd "$(dirname "$0")/.."

echo "📁 Current directory: $(pwd)"

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

echo "🔍 Validating database connection..."
python3 scripts/validate.py

if [ $? -eq 0 ]; then
    echo "✅ Database connection validated"
else
    echo "❌ Database connection validation failed"
    exit 1
fi

echo "🚀 Starting database deployment..."
python3 scripts/deploy.py

if [ $? -eq 0 ]; then
    echo "✅ Database deployment completed successfully!"
    echo "📊 Running final validation..."
    python3 scripts/validate.py
else
    echo "❌ Database deployment failed"
    exit 1
fi

echo "🎉 All done! Database is ready to use."
