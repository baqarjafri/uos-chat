#!/bin/sh
echo "=== Starting Backend Application ==="

# Run migration
echo "Step 1: Running database migration..."
python migrate.py
if [ $? -ne 0 ]; then
    echo "ERROR: Migration failed"
    exit 1
fi
echo "✅ Migration completed successfully"

# Start FastAPI
echo "Step 2: Starting FastAPI application..."
echo "Port: ${PORT:-8000}"
echo "Host: 0.0.0.0"
echo "================================"

uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
