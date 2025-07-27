# API Documentation

The Document Agent Service exposes functionality through two separate API services, each with distinct responsibilities and security models.

## API Architecture

The system provides two FastAPI-based services:

1. **Agent API** (Port 8000): Public-facing interface for document interaction
2. **Admin API** (Port 8001): Administrative interface with restricted access

## 1. Agent API Service (Port 8000)

The Agent API provides document interaction capabilities for end users. It's implemented in `app/api/agent_app.py` and `app/api/router_agent.py`.

### Authentication

- Uses Bearer token authentication
- Tokens are managed by the Admin API
- All endpoints require a valid token except health checks
- Format: `Authorization: Bearer YOUR_TOKEN`

### Endpoints

#### Document Management

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/agent/docs` | POST | Upload a document for processing | `file`: Document file (max 2MB) |
| `/agent/docs/{filename}` | DELETE | Delete a document | `filename`: Document filename |

#### Document Querying

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/agent/docs/{doc_id}/summary` | GET | Get a summary of a document | `doc_id`: Document ID, `length`: Summary length (50-500) |
| `/agent/docs/{doc_id}/topics` | GET | Get topics for a document | `doc_id`: Document ID |
| `/agent/docs/{doc_id}/qa` | POST | Answer a question about a specific document | `doc_id`: Document ID, `question`: User question, `session_id` (optional) |
| `/agent/qa` | POST | Answer a general question about any document | `question`: User question, `doc_id` (optional): Specific document, `session_id` (optional) |

#### System

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/health` | GET | Health check endpoint | None |
| `/` | GET | API information | None |

### Example Requests

```bash
# Upload a document
curl -X POST "http://localhost:8000/agent/docs" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"

# Ask a question about a document
curl -X POST "http://localhost:8000/agent/docs/doc123/qa" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "session_id": "session123"}'

# Ask a general question
curl -X POST "http://localhost:8000/agent/qa" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "doc_id": "doc123"}'
```

## 2. Admin API Service (Port 8001)

The Admin API provides user management and system administration capabilities. It's implemented in `app/api/admin_app.py` and `app/api/router_users.py`.

### Security

- Restricted to localhost by default for security
- No external authentication required (protected by network isolation)
- Designed for administrative operations only

### Admin-Only Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/admin/users/` | POST | Create a new user | `email`, `name`, `token_validity_hours` |
| `/admin/users/list` | GET | List all users | `limit`, `skip` |
| `/admin/users/{user_id}` | GET | Get user details | `user_id` |
| `/admin/users/{user_id}` | DELETE | Delete a user | `user_id` |
| `/admin/users/{user_id}/refresh-token` | POST | Refresh user's token | `user_id`, `token_validity_hours` |
| `/admin/users/{user_id}/history` | GET | Get user's question history | `user_id`, `limit` |
| `/admin/users/by-email/{email}` | GET | Find user by email | `email` |
| `/admin/users/{user_id}/add-qa` | POST | Add Q&A to user history | `user_id`, `question`, `answer` |
| `/admin/users/stats/overview` | GET | Get system statistics (Note: Implementation needed) | None |

### User-Facing Endpoints (with token)

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/admin/users/me` | GET | Get current user profile | None |
| `/admin/users/me/history` | GET | Get current user's history | `limit` |
| `/admin/users/me/refresh-token` | POST | Refresh current user's token | `token_validity_hours` |
| `/admin/users/me` | PUT | Update current user's profile | `name` |
| `/admin/users/me` | DELETE | Delete current user's account | None |
| `/admin/users/validate-token` | POST | Validate a token | None |

### Example Requests

```bash
# Create a new user
curl -X POST "http://localhost:8001/admin/users/" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "Example User", "token_validity_hours": 24}'

# List all users
curl -X GET "http://localhost:8001/admin/users/list?limit=10&skip=0"
```

## API Models

### Agent API Models

#### QARequest

```json
{
  "question": "string",
  "doc_id": "string (optional)",
  "session_id": "string (optional)"
}
```

#### QAResponse

```json
{
  "answer": "string",
  "doc_id": "string (optional)",
  "session_id": "string"
}
```

#### AgentResponse

```json
{
  "result": "string",
  "success": "boolean (default: true)",
  "message": "string (optional)"
}
```

### Admin API Models

#### CreateUserRequest

```json
{
  "email": "string (email)",
  "name": "string",
  "token_validity_hours": "integer (default: 24)"
}
```

#### CreateUserResponse

```json
{
  "user_id": "string",
  "email": "string",
  "name": "string",
  "token": "string",
  "expires_at": "string (datetime)",
  "message": "string"
}
```

#### UpdateUserRequest

```json
{
  "name": "string (optional)"
}
```

#### AddQARequest

```json
{
  "question": "string",
  "answer": "string"
}
```

## API Documentation

Both APIs provide comprehensive OpenAPI documentation when the services are running:
- Agent API: available at `/docs` 
- Admin API: available at `/admin/docs` and `/admin/redoc`

This interactive documentation allows testing endpoints directly from the browser.
