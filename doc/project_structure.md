# Project Structure

The Document Agent Service follows a modular Python package structure organized by component responsibility.

## Directory Structure

```
document_agent_service/
├── app/                   # Main application package
│   ├── __init__.py
│   ├── agent/             # LLM agent implementation
│   │   ├── __init__.py
│   │   ├── agent.py       # Main agent implementation
│   │   ├── llm_backend.py # LLM provider abstraction
│   │   └── tools.py       # Agent tool definitions
│   ├── api/               # API endpoints
│   │   ├── __init__.py
│   │   ├── admin_app.py   # Admin API application
│   │   ├── agent_app.py   # Main agent API application
│   │   ├── router_agent.py # Agent endpoint routes
│   │   └── router_users.py # User management routes
│   ├── core/              # Core application components
│   │   ├── __init__.py
│   │   └── config.py      # Configuration management
│   ├── db/                # Database abstraction
│   │   ├── __init__.py
│   │   ├── factory.py     # Database factory pattern
│   │   ├── interfaces.py  # Abstract database interfaces
│   │   ├── user_handler.py # User data management
│   │   └── mongo/         # MongoDB implementation
│   ├── ingestion/         # Document ingestion pipeline
│   │   ├── __init__.py
│   │   ├── loader.py      # Document loading logic
│   │   ├── watch_service.py # File system watcher service
│   │   ├── watcher.py     # Watcher implementation
│   │   └── parsers/       # Document format parsers
│   └── models/            # Data models
│       ├── __init__.py
│       ├── api_models.py  # API request/response models
│       ├── document_models.py # Document data models
│       └── user_models.py # User data models
├── data/                  # Data storage
│   └── inbox/             # Document inbox folder
├── doc/                   # Documentation
│   ├── architecture.md    # System architecture details
│   ├── api.md             # API documentation
│   ├── configuration.md   # Configuration guide
│   ├── deployment.md      # Deployment instructions
│   ├── development.md     # Development guide
│   └── features.md        # Feature documentation
├── scripts/               # Helper scripts
├── docker-compose.yml     # Docker services definition
├── Dockerfile             # Container build definition
├── pyproject.toml         # Project metadata and dependencies
└── README.md              # Project documentation
```

## Key Technologies

The system leverages several key technologies to provide its functionality:

### Core Technologies

- **Python 3.11+**: Modern Python with support for async/await patterns and type hints
- **Docker**: Container platform for consistent deployment and isolation
- **PDM**: Modern Python package and dependency manager
- **FastAPI**: High-performance async web framework for APIs
- **MongoDB**: Document-oriented NoSQL database
- **Uvicorn**: ASGI server for running FastAPI applications

### AI and Document Processing

- **LangChain**: Framework for building LLM applications with tools and agents
- **LangChain Tools**: Custom tools for document operations and querying
- **Multiple LLM Providers**:
  - OpenAI (GPT models)
  - Google Generative AI (Gemini)
  - Ollama (self-hosted models)
- **Document Processing**:
  - PyPDF: PDF parsing and text extraction
  - python-docx: Microsoft Word document processing
  - Watchdog: Real-time file system event monitoring

### Development Tools

- **Pydantic**: Data validation and settings management
- **Motor**: Async MongoDB driver for Python
- **Python-dotenv**: Environment variable management
- **Pytest**: Testing framework with async support
