#!/bin/bash
set -e

# Configuration
PROJECT_ID="codetomarket"
IMAGE_NAME="codebase-to-llm-api"
REGION="europe-west1"
REPOSITORY="docker-repo"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building and pushing Docker image to Google Cloud Artifact Registry${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}Setting Google Cloud project to ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Configure Docker to use gcloud as a credential helper
echo -e "${YELLOW}Configuring Docker authentication${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build the Docker image
echo -e "${YELLOW}Building Docker image${NC}"
docker build -f docker/Dockerfile -t ${IMAGE_NAME}:latest .

# Tag the image for Artifact Registry
FULL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest"
echo -e "${YELLOW}Tagging image as ${FULL_IMAGE_NAME}${NC}"
docker tag ${IMAGE_NAME}:latest ${FULL_IMAGE_NAME}

# Push the image to Artifact Registry
echo -e "${YELLOW}Pushing image to Artifact Registry${NC}"
docker push ${FULL_IMAGE_NAME}

echo -e "${GREEN}Successfully built and pushed Docker image!${NC}"
echo -e "${GREEN}Image: ${FULL_IMAGE_NAME}${NC}"

# Optional: Clean up local images to save space
read -p "Do you want to remove local Docker images to save space? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Removing local images${NC}"
    docker rmi ${IMAGE_NAME}:latest ${FULL_IMAGE_NAME} || true
    echo -e "${GREEN}Local images removed${NC}"
fi

echo -e "${GREEN}Build and push completed successfully!${NC}"
