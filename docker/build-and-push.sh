#!/bin/bash
set -e

# Configuration
PROJECT_ID="codetomarket"
API_IMAGE_NAME="codebase-to-llm-api"
DOWNLOADER_IMAGE_NAME="codebase-to-llm-downloader"
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

# Build the API Docker image
echo -e "${YELLOW}Building API Docker image${NC}"
docker build -f docker/Dockerfile -t ${API_IMAGE_NAME}:latest .

# Tag the API image for Artifact Registry
API_FULL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${API_IMAGE_NAME}:latest"
echo -e "${YELLOW}Tagging API image as ${API_FULL_IMAGE_NAME}${NC}"
docker tag ${API_IMAGE_NAME}:latest ${API_FULL_IMAGE_NAME}

# Push the API image to Artifact Registry
echo -e "${YELLOW}Pushing API image to Artifact Registry${NC}"
docker push ${API_FULL_IMAGE_NAME}

echo -e "${GREEN}Successfully built and pushed API Docker image!${NC}"
echo -e "${GREEN}API Image: ${API_FULL_IMAGE_NAME}${NC}"

# Build the Downloader Docker image
echo -e "${YELLOW}Building Downloader Docker image${NC}"
docker build -f docker/Dockerfile.downloader -t ${DOWNLOADER_IMAGE_NAME}:latest .

# Tag the Downloader image for Artifact Registry
DOWNLOADER_FULL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${DOWNLOADER_IMAGE_NAME}:latest"
echo -e "${YELLOW}Tagging Downloader image as ${DOWNLOADER_FULL_IMAGE_NAME}${NC}"
docker tag ${DOWNLOADER_IMAGE_NAME}:latest ${DOWNLOADER_FULL_IMAGE_NAME}

# Push the Downloader image to Artifact Registry
echo -e "${YELLOW}Pushing Downloader image to Artifact Registry${NC}"
docker push ${DOWNLOADER_FULL_IMAGE_NAME}

echo -e "${GREEN}Successfully built and pushed Downloader Docker image!${NC}"
echo -e "${GREEN}Downloader Image: ${DOWNLOADER_FULL_IMAGE_NAME}${NC}"


echo -e "${GREEN}Build and push completed successfully!${NC}"
