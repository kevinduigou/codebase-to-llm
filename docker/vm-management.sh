#!/bin/bash
set -e

# Function to show usage
show_usage() {
    echo "Usage: $0 [dev|prod] [start|stop|restart|logs|ssh|status]"
    echo "  Environment:"
    echo "    dev  - Manage development VM"
    echo "    prod - Manage production VM"
    echo "  Action:"
    echo "    start   - Start the VM and downloader service"
    echo "    stop    - Stop the VM"
    echo "    restart - Restart the downloader service"
    echo "    logs    - Show downloader service logs"
    echo "    ssh     - SSH into the VM"
    echo "    status  - Show VM and service status"
    echo ""
    echo "Examples:"
    echo "  $0 dev start     # Start development VM"
    echo "  $0 prod logs     # Show production downloader logs"
    echo "  $0 dev ssh       # SSH into development VM"
    exit 1
}

# Check arguments
if [ $# -ne 2 ]; then
    echo "Error: Both environment and action arguments are required"
    show_usage
fi

ENVIRONMENT=$1
ACTION=$2

# Validate environment argument
if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "Error: Invalid environment '$ENVIRONMENT'. Must be 'dev' or 'prod'"
    show_usage
fi

# Validate action argument
if [ "$ACTION" != "start" ] && [ "$ACTION" != "stop" ] && [ "$ACTION" != "restart" ] && [ "$ACTION" != "logs" ] && [ "$ACTION" != "ssh" ] && [ "$ACTION" != "status" ]; then
    echo "Error: Invalid action '$ACTION'. Must be 'start', 'stop', 'restart', 'logs', 'ssh', or 'status'"
    show_usage
fi

# Configuration
PROJECT_ID="codetomarket"
ZONE="europe-west1-b"

# Environment-specific configuration
if [ "$ENVIRONMENT" = "dev" ]; then
    DOWNLOADER_VM_NAME="codebase-downloader-vm-dev"
elif [ "$ENVIRONMENT" = "prod" ]; then
    DOWNLOADER_VM_NAME="codebase-downloader-vm"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Set the project
gcloud config set project ${PROJECT_ID} --quiet

# Execute action
case $ACTION in
    "start")
        echo -e "${YELLOW}Starting VM ${DOWNLOADER_VM_NAME}...${NC}"
        gcloud compute instances start ${DOWNLOADER_VM_NAME} --zone=${ZONE}
        echo -e "${GREEN}VM started successfully!${NC}"
        
        # Wait for VM to be ready
        echo -e "${YELLOW}Waiting for VM to be ready...${NC}"
        sleep 15
        
        # Get VM external IP
        VM_EXTERNAL_IP=$(gcloud compute instances describe ${DOWNLOADER_VM_NAME} --zone=${ZONE} --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
        echo -e "${GREEN}VM External IP: ${VM_EXTERNAL_IP}${NC}"
        echo -e "${GREEN}Downloader Service URL: http://${VM_EXTERNAL_IP}:8080${NC}"
        ;;
        
    "stop")
        echo -e "${YELLOW}Stopping VM ${DOWNLOADER_VM_NAME}...${NC}"
        gcloud compute instances stop ${DOWNLOADER_VM_NAME} --zone=${ZONE}
        echo -e "${GREEN}VM stopped successfully!${NC}"
        ;;
        
    "restart")
        echo -e "${YELLOW}Restarting downloader service on ${DOWNLOADER_VM_NAME}...${NC}"
        gcloud compute ssh ${DOWNLOADER_VM_NAME} --zone=${ZONE} --command="
            CONTAINER_ID=\$(sudo docker ps --filter name=klt-${DOWNLOADER_VM_NAME} --format '{{.ID}}')
            if [ -n \"\$CONTAINER_ID\" ]; then
                sudo docker restart \$CONTAINER_ID
            else
                echo 'No container found to restart'
                exit 1
            fi
        "
        echo -e "${GREEN}Downloader service restarted successfully!${NC}"
        ;;
        
    "logs")
        echo -e "${YELLOW}Showing logs for downloader service on ${DOWNLOADER_VM_NAME}...${NC}"
        gcloud compute ssh ${DOWNLOADER_VM_NAME} --zone=${ZONE} --command="
            CONTAINER_ID=\$(sudo docker ps --filter name=klt-${DOWNLOADER_VM_NAME} --format '{{.ID}}')
            if [ -n \"\$CONTAINER_ID\" ]; then
                sudo docker logs -f --tail=100 \$CONTAINER_ID
            else
                echo 'No container found'
                exit 1
            fi
        "
        ;;
        
    "ssh")
        echo -e "${YELLOW}Connecting to ${DOWNLOADER_VM_NAME}...${NC}"
        gcloud compute ssh ${DOWNLOADER_VM_NAME} --zone=${ZONE}
        ;;
        
    "status")
        echo -e "${YELLOW}Checking status of ${DOWNLOADER_VM_NAME}...${NC}"
        
        # VM status
        VM_STATUS=$(gcloud compute instances describe ${DOWNLOADER_VM_NAME} --zone=${ZONE} --format="value(status)" 2>/dev/null || echo "NOT_FOUND")
        echo -e "${BLUE}VM Status: ${VM_STATUS}${NC}"
        
        if [ "$VM_STATUS" = "RUNNING" ]; then
            # Get VM external IP
            VM_EXTERNAL_IP=$(gcloud compute instances describe ${DOWNLOADER_VM_NAME} --zone=${ZONE} --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
            echo -e "${BLUE}VM External IP: ${VM_EXTERNAL_IP}${NC}"
            
            # Container status
            CONTAINER_STATUS=$(gcloud compute ssh ${DOWNLOADER_VM_NAME} --zone=${ZONE} --command="
                sudo docker ps --filter name=klt-${DOWNLOADER_VM_NAME} --format 'table {{.Status}}' | tail -n +2
            " 2>/dev/null || echo "UNKNOWN")
            echo -e "${BLUE}Container Status: ${CONTAINER_STATUS}${NC}"
            
            # Check if Celery worker is ready
            echo -e "${YELLOW}Checking Celery worker status...${NC}"
            CELERY_STATUS=$(gcloud compute ssh ${DOWNLOADER_VM_NAME} --zone=${ZONE} --command="
                CONTAINER_ID=\$(sudo docker ps --filter name=klt-${DOWNLOADER_VM_NAME} --format '{{.ID}}')
                if [ -n \"\$CONTAINER_ID\" ]; then
                    sudo docker logs \$CONTAINER_ID 2>/dev/null | grep -c 'celery.*ready' || echo '0'
                else
                    echo '0'
                fi
            " 2>/dev/null || echo "0")
            
            if [ "$CELERY_STATUS" -gt 0 ]; then
                echo -e "${GREEN}✓ Celery Downloader Worker is ready and processing tasks${NC}"
            else
                echo -e "${RED}✗ Celery Downloader Worker is not ready${NC}"
            fi
        elif [ "$VM_STATUS" = "TERMINATED" ]; then
            echo -e "${YELLOW}VM is stopped. Use 'start' action to start it.${NC}"
        elif [ "$VM_STATUS" = "NOT_FOUND" ]; then
            echo -e "${RED}VM not found. Deploy the downloader first.${NC}"
        fi
        ;;
esac
