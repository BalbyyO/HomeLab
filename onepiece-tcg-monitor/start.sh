#!/bin/bash

# One Piece TCG Price Monitor - Quick Start Script

echo "=================================================="
echo "  One Piece TCG Price Monitor"
echo "=================================================="
echo ""

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "❌ Error: config.yaml not found!"
    echo "Please create config.yaml before running."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "✅ Configuration file found"
echo "✅ Docker is running"
echo ""

# Build and start
echo "Building and starting container..."
docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "  ✅ One Piece TCG Monitor Started!"
    echo "=================================================="
    echo ""
    echo "The monitor is now running in the background."
    echo ""
    echo "Useful commands:"
    echo "  • View logs:     docker-compose logs -f"
    echo "  • Stop monitor:  docker-compose down"
    echo "  • Restart:       docker-compose restart"
    echo ""
    echo "Showing recent logs (Ctrl+C to exit logs)..."
    echo ""
    sleep 2
    docker-compose logs -f
else
    echo ""
    echo "❌ Failed to start container"
    echo "Check the error messages above"
    exit 1
fi
