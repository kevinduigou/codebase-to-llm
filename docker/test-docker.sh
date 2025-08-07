#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Docker setup for FastAPI application${NC}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -f docker/Dockerfile -t codebase-to-llm-test .

# Run a quick test
echo -e "${YELLOW}Running container test...${NC}"
CONTAINER_ID=$(docker run -d -p 8001:8000 codebase-to-llm-test)

# Wait for the container to start
echo -e "${YELLOW}Waiting for container to start...${NC}"
sleep 10

# Test if the API is responding
echo -e "${YELLOW}Testing API health...${NC}"
if curl -f http://localhost:8001/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is responding correctly${NC}"
    TEST_PASSED=true
else
    echo -e "${RED}✗ API is not responding${NC}"
    TEST_PASSED=false
fi

# Show container logs
echo -e "${YELLOW}Container logs:${NC}"
docker logs $CONTAINER_ID

# Clean up
echo -e "${YELLOW}Cleaning up...${NC}"
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID
docker rmi codebase-to-llm-test

if [ "$TEST_PASSED" = true ]; then
    echo -e "${GREEN}✓ Docker setup test passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Docker setup test failed!${NC}"
    exit 1
fi
