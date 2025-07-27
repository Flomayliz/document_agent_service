# Deployment and Configuration

This guide covers the deployment of the Document Agent Service using Docker and its configuration options.

## Docker Deployment Architecture

The system is deployed as a set of containerized microservices, each with specific responsibilities and isolation. This containerized approach provides several benefits:

1. **Isolation**: Each component runs in its own environment with explicit dependencies
2. **Scalability**: Individual services can be scaled independently based on load
3. **Portability**: Consistent behavior across different deployment environments
4. **Resource Efficiency**: Containers share kernel resources while maintaining isolation

## Service Components

The Docker setup consists of the following components:

- **MongoDB Container (llm_doc_mongo)**:
  - Runs on port 27017
  - Persists data in a named volume for durability
  - Configured with database name "llm_doc_poc"

- **API Service (llm_doc_api)**:
  - Runs on port 8000
  - Provides the main document querying interface
  - Mounts the inbox folder for document access
  - Containerized FastAPI application

- **Admin Service (llm_doc_admin)**:
  - Runs on port 8001
  - Provides administrative functions
  - Restricted to authorized administrators
  - Separate container for security isolation

- **Watcher Service (llm_doc_watcher)**:
  - Monitors the document inbox folder
  - Triggers document processing on changes
  - Works in conjunction with the API service
  - Dedicated container for file system monitoring

## Deployment Commands

```bash
# Start all services
docker compose up -d

# View running containers
docker ps

# View logs for a specific service
docker logs llm_doc_api

# Stop all services
docker compose down

# Stop services and remove volumes
docker compose down -v
```

## Volumes and Data Persistence

The system uses Docker volumes to ensure data persistence:

- `mongo_data`: Stores MongoDB data files
- `./data/inbox:/data/inbox`: Maps the local inbox folder to the container for document monitoring

## Network Configuration

All services run on a private Docker network with the following ports exposed to the host:

- `27017`: MongoDB (optional, can be restricted to internal network)
- `8000`: Agent API (public facing)
- `8001`: Admin API (restricted access)

## Security Considerations

1. **API Access Control**:
   - The Agent API uses token-based authentication
   - The Admin API should be restricted to trusted networks

2. **Container Isolation**:
   - Each service runs in its own container
   - Services communicate through defined APIs
