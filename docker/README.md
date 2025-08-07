# Docker Setup for FastAPI Application

This directory contains Docker configuration files to containerize the FastAPI application.

## Files Overview

- `Dockerfile`: Main Docker image definition
- `docker-compose.yml`: Docker Compose configuration for easy deployment
- `entrypoint.sh`: Startup script that initializes the database and starts the application
- `.dockerignore`: Files and directories to exclude from Docker build context

## Quick Start

### Using Docker Compose (Recommended)

1. Build and start the application:
```bash
cd docker
docker-compose up --build
```

2. The application will be available at `http://localhost:8000`
3. API documentation will be available at `http://localhost:8000/docs`

### Using Docker directly

1. Build the Docker image:
```bash
docker build -f docker/Dockerfile -t codebase-to-llm-api .
```

2. Run the container:
```bash
docker run -p 8000:8000 -v codebase_data:/app/data codebase-to-llm-api
```

## Configuration

### Environment Variables

- `DATABASE_URL`: Database connection string (default: `sqlite:///./data/users.db`)

### Database Options

#### SQLite (Default)
The application uses SQLite by default, which is suitable for development and small deployments.

#### PostgreSQL (Optional)
To use PostgreSQL instead:

1. Uncomment the PostgreSQL service in `docker-compose.yml`
2. Update the environment variable:
```yaml
environment:
  - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/codebase_to_llm
```

## Data Persistence

- SQLite database and application data are stored in the `app_data` Docker volume
- Data persists between container restarts

## Health Check

The application includes a health check that verifies the API is responding correctly.

## Development

For development with live code reloading:

1. Mount the source code as a volume:
```bash
docker run -p 8000:8000 -v $(pwd)/src:/app/src -v codebase_data:/app/data codebase-to-llm-api
```

## API Endpoints

Once running, the main endpoints include:

- `POST /register` - Register a new user
- `POST /token` - Login and get access token
- `GET /docs` - Interactive API documentation
- `POST /api-keys` - Add API keys
- `POST /context-buffer/file` - Add files to context buffer
- `POST /llm-response` - Generate LLM responses

## Troubleshooting

### Container won't start
- Check logs: `docker-compose logs fastapi-app`
- Ensure port 8000 is not already in use

### Database issues
- Remove the volume to reset: `docker volume rm docker_app_data`
- Check database permissions in the container

### Build issues
- Clear Docker cache: `docker system prune -a`
- Ensure all dependencies are properly specified in `pyproject.toml`
