# System Architecture

The Document Agent Service follows a modular design with clear separation of concerns. This approach ensures maintainability, extensibility, and scalability. Each component operates independently while communicating through well-defined interfaces.

## Architecture Overview

![System Architecture](/doc/images/architecture-diagram.png)

The system consists of four primary modules:

## 1. Ingestion Module

The ingestion module serves as the system's document acquisition and processing pipeline, functioning as the first stage in the document intelligence workflow.

### Key Components

- **Document Watcher Service**: 
  - Implemented using the `watchdog` library to monitor filesystem events in real-time
  - Runs as a standalone service that can detect creation, modification, and deletion of files
  - Designed with an event-driven architecture to minimize resource usage while providing immediate processing
  - Located in `app/ingestion/watch_service.py` and `app/ingestion/watcher.py`

- **Document Parser System**: 
  - Uses a registry-based architecture for document format handling
  - Each document type (PDF, DOCX, etc.) has a dedicated parser implementation
  - Parsers extract raw text and metadata using specialized libraries:
    - PDF: PyPDF for text extraction with page boundary preservation
    - Word: python-docx for structured content extraction including headers and formatting
    - Plain text: Native Python with encoding detection for maximum compatibility
  - Registry system in `app/ingestion/parsers/__init__.py` enables automatic parser selection

- **Information Extraction Pipeline**:
  - After text extraction, processes documents through multiple enrichment stages:
    1. Metadata extraction (file size, creation date, modification date)
    2. Content analysis for keyword extraction (using NLP techniques)
    3. Topic identification (using clustering or LLM classification)
    4. Automatic summarization (using extractive and abstractive methods)
  - Each stage adds valuable context that improves the agent's response quality

### Architectural Decisions

- **Event-driven Design**: Chosen to provide immediate processing while minimizing system load. The watcher only activates processing when documents change, making the system efficient even with large repositories.

- **Parser Registry Pattern**: Enables extensibility by allowing new document formats to be supported through the addition of new parser classes without modifying existing code. This follows the Open/Closed principle of software design.

- **Uniform Document Representation**: All parsers produce a standardized `ParsedDocument` object regardless of the original format. This decision decouples the downstream processing from the specifics of document formats, allowing the rest of the system to work with a consistent data structure.

- **Local Folder Implementation**: The current implementation monitors a local folder (`/data/inbox`), but the modular design allows for alternative source implementations such as cloud storage providers (S3, Google Drive, etc.) without affecting the rest of the system.

## 2. Database Module

The database module provides persistence, caching, and retrieval capabilities for both document content and user information, serving as the system's central data repository.

### Key Components

- **Factory Pattern Implementation**:
  - Located in `app/db/factory.py`
  - Implements the Abstract Factory pattern to provide database independence
  - Defines abstract interfaces in `app/db/interfaces.py` that concrete implementations must satisfy
  - Currently supports MongoDB but designed to allow other database backends

- **Document Repository**:
  - Stores processed documents with comprehensive metadata
  - Implements efficient search and retrieval capabilities
  - Maintains relationships between documents for comparative analysis
  - Uses indexing strategies optimized for text search performance

- **User Management System**:
  - Manages user accounts, authentication tokens, and permissions
  - Stores conversation history for context retention between sessions
  - Implements token-based authentication with configurable expiration
  - Located in `app/db/user_handler.py`

### Architectural Decisions

- **Factory Pattern**: This pattern was chosen to allow the system to work with different database backends without modification to the core logic. This decision supports both development flexibility (using different databases in development and production) and deployment flexibility (adapting to existing infrastructure constraints).

- **Document Caching Strategy**: Documents are pre-processed and stored in a structured format to:
  1. Reduce response latency by eliminating the need for real-time document parsing
  2. Decrease LLM token usage by providing only relevant document portions
  3. Enable sophisticated filtering and search capabilities across the document corpus
  4. Allow for stateful conversations that reference previous document queries

- **MongoDB Selection**: MongoDB was chosen as the initial database implementation for several reasons:
  1. Document-oriented structure maps naturally to the variable document formats
  2. Schema flexibility accommodates different document types without migration challenges
  3. Horizontal scaling capabilities support growing document repositories
  4. Rich query language enables sophisticated document filtering and search
  5. Readily available as a containerized solution for simplified deployment

## 3. Agent Module

The agent module forms the intelligent core of the system, interpreting user queries, planning information retrieval, and synthesizing responses based on document content.

### Key Components

- **LangChain Agent Framework**:
  - Implements a tool-based agent using the LangChain framework
  - Located primarily in `app/agent/agent.py`
  - Uses a sophisticated prompt system that guides the LLM in tool selection and response generation

- **Flexible LLM Backend**:
  - Supports multiple LLM providers through a provider-agnostic interface
  - Current implementation in `app/agent/llm_backend.py` supports:
    - OpenAI (GPT models) for high-quality but proprietary inference
    - Google Gemini for alternative commercial provider
    - Ollama for self-hosted open-source models (reducing operational costs)
  - Selection controlled through configuration rather than code changes

- **Specialized Tool Suite**:
  - Tools defined in `app/agent/tools.py` with specific capabilities:
    - `list_docs`: Returns a comprehensive inventory of available documents with metadata
    - `get_topics`: Retrieves the main themes and subject areas of a document
    - `get_document`: Fetches the complete content of a specific document
    - `document_stats`: Provides statistical analysis of document structure and content
    - `compare_documents`: Performs comparative analysis between two documents
    - `search`: Enables semantic and keyword search across all documents
    - `about_leslie`: Retrieves information about the system creator
    - `get_user_history`: Accesses the conversation history for contextual awareness

### Architectural Decisions

- **Tool-Based Agent Architecture**: This architecture was chosen because it:
  1. Provides a structured approach to complex problem-solving
  2. Allows the LLM to break down complex queries into manageable sub-tasks
  3. Creates an extensible system where new capabilities can be added as tools
  4. Improves transparency by making agent reasoning explicit through tool selection

- **Provider-Agnostic LLM Interface**: The system was designed to work with multiple LLM providers to:
  1. Avoid vendor lock-in with any single LLM provider
  2. Allow cost optimization by selecting appropriate models for different tasks
  3. Support private deployments with self-hosted models when data sensitivity is a concern
  4. Future-proof the system as new, more capable LLMs become available

- **Specialized Document Tools**: Rather than creating a general RAG system, specialized tools were developed to:
  1. Provide more targeted and accurate document information retrieval
  2. Support specific document operations like comparison and statistical analysis
  3. Guide the LLM toward optimal information gathering strategies
  4. Reduce hallucination by constraining the LLM to verified document content

## 4. API Module

The API module exposes the system's capabilities through standardized interfaces, enabling integration with external systems and providing user access points.

### Key Components

- **FastAPI Implementation**:
  - Builds on the high-performance FastAPI framework
  - Split into separate applications for agent interaction and administration
  - Located in `app/api/agent_app.py` and `app/api/admin_app.py`
  - Leverages automatic OpenAPI documentation generation

- **Authentication System**:
  - Implements token-based authentication with Bearer token scheme
  - Includes middleware for request authorization
  - Manages token lifecycle (creation, validation, revocation)

- **Dual Server Architecture**:
  - Agent API (port 8000): User-facing interface for document queries
  - Admin API (port 8001): Administrative functions with restricted access
  - Separation provides security isolation between user and administrative functions

### Architectural Decisions

- **FastAPI Selection**: FastAPI was chosen over alternatives like Flask or Django for:
  1. Superior performance through asynchronous request handling
  2. Native support for modern Python features (type hints, async/await)
  3. Automatic API documentation generation
  4. Built-in request validation and serialization

- **Dual Server Approach**: The separation between agent and admin APIs was implemented to:
  1. Apply different security models to each interface (public vs. administrative)
  2. Allow independent scaling of user and administrative traffic
  3. Enable different deployment strategies (e.g., admin API only accessible internally)
  4. Provide clearer separation of concerns in the codebase
