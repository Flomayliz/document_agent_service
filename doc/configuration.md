# Configuration Guide

The Document Agent Service uses environment variables for configuration, making it flexible and adaptable to different deployment scenarios. This guide explains all available configuration options.

## Configuration File

The project uses a `.env` file for configuration. The environment file path can be customized using the `ENV_PATH` environment variable, otherwise it defaults to `.env` in the project root.

## Core Configuration Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `DEBUG` | Enable debug mode | `false` | `true` |
| `WATCH_FOLDER` | Directory to monitor for documents | `/data/inbox` | `/app/data/inbox` |
| `MAX_TOKENS_DOC` | Maximum tokens per document for processing | `15000` | `20000` |

## LLM Provider Configuration

| Parameter | Description | Default | Required For |
|-----------|-------------|---------|-------------|
| `MODEL_BACKEND` | LLM provider selection | `openai` | All |
| `OPENAI_API_KEY` | OpenAI API key | `""` (empty string) | OpenAI backend |
| `GEMINI_API_KEY` | Google Gemini API key | `""` (empty string) | Gemini backend |
| `OLLAMA_MODEL` | Ollama model name | `deepseek-67b` | Ollama backend |

### Supported Model Backends

- `openai`: Uses OpenAI GPT-3.5-Turbo model (requires API key)
- `gemini`: Uses Google Gemini 2.0 Flash model (requires API key)
- `ollama`: Uses self-hosted models via Ollama (requires Ollama running locally)

## Database Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `MONGO_URI` | MongoDB connection URI | `mongodb://mongo:27017` |
| `MONGO_DB_NAME` | MongoDB database name | `llm_doc_poc` |


## Complete Configuration Example

```bash
MODEL_BACKEND=gemini
OPENAI_API_KEY='YOUR_OPENAI_API_KEY'
GEMINI_API_KEY='YOUR_GEMINI_API_KEY'

OLLAMA_MODEL=deepseek-67b

# API Configuration
API_TOKEN=demo-token

# Database Configuration
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=llm_doc_poc

# Watcher Configuration
WATCH_FOLDER=/data/inbox

# Processing Configuration
MAX_TOKENS_DOC=15000

# Development
DEBUG=true
```

## Configuration Precedence

The system loads configuration in the following order of precedence (highest to lowest):

1. Environment variables set in the runtime environment
2. Values from the `.env` file
3. Default values defined in the application code

## Sensitive Configuration

When deploying in production, consider these security practices:

1. Do not commit API keys to version control
2. Use a secure method to provide the `.env` file or environment variables
3. Set restrictive permissions on the `.env` file
4. Consider using a secrets manager for production deployments

## Configuration Management

The configuration system is implemented in `app/core/config.py` using Pydantic's `BaseSettings` class (specifically `pydantic_settings.BaseSettings`), which provides:

- Type validation for configuration values
- Automatic environment variable loading
- Default values for optional settings
- Settings caching via `@lru_cache`
