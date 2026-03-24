#!/bin/bash

echo "=================================================="
echo "  🗺️  Find My - Location Tracker"
echo "  Starting Web Application..."
echo "=================================================="
echo ""

# Start the web server
cd /app/web
python3 server.py

echo ""
echo "=================================================="
echo "  Server stopped."
echo "=================================================="
