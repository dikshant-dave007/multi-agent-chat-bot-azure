# Multi-Agent Chat Bot POC

A Semantic Kernel-based multi-agent chatbot system built with Python, FastAPI, Semantic Kernel, and Azure services. Demonstrates intelligent intent detection and agent routing for specialized tasks.

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Layer                            │
│              Chat API - Process user messages                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Intent Detection Service                         │
│           (LLM-based content classification)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────────┐
            ▼                 ▼                     ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Greeting Agent   │ │ Researcher Agent │ │ Email Agent      │
│                  │ │                  │ │                  │
│ • User salutation│ │ • Topic research │ │ • Email writing  │
│ • Conversations │ │ • Knowledge docs │ │ • Professional   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼
┌──────────────────┐ ┌──────────────────────────┐
│ Database Agent   │ │ Event & Celebration      │
│                  │ │ Agent                    │
│ • CRUD ops       │ │ • Event management       │
│ • Cosmos DB      │ │ • Celebration posts      │
│ • Data queries   │ │ • Special occasions      │
└──────────────────┘ └──────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Semantic        │ │  Azure Cosmos DB │ │   Azure OpenAI   │
│  Kernel          │ │                  │ │                  │
│  • LLM queries   │ │ • Task state     │ │ • GPT-4 calls    │
│  • Prompts       │ │ • Messages       │ │ • Embeddings     │
│  • Tools         │ │ • Cache data     │ │ • Completions    │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

## Key Design Decisions

### 1. Semantic Kernel-Based Architecture
- **Intent Detection**: LLM-driven message classification system routes queries to appropriate agents
- **Specialized Agents**: Five purpose-built agents handle distinct use cases
- **Pluggable Design**: New agents can be easily added by extending `BaseSemanticAgent`
- **No Hard Dependencies**: Agents communicate through a centralized orchestrator

### 2. Intelligent Intent Routing
- **Natural Language Classification**: Uses Azure OpenAI to understand user intent
- **Confidence Scoring**: Intent detection includes confidence metrics
- **Fallback Handling**: Unknown intents route to Greeting Agent for clarification
- **Context Awareness**: Maintains conversation history for better intent detection

### 3. Agent Specialization
- **Greeting Agent**: Handles conversational greetings and casual interactions
- **Researcher Agent**: Performs knowledge-based research using LLM
- **Email Writer Agent**: Generates professional emails with context
- **Database Agent**: Manages CRUD operations on Azure Cosmos DB
- **Event & Celebration Agent**: Creates event posts and celebration content

### 4. Asynchronous Processing
- **Async-First Design**: All I/O operations use asyncio
- **Non-Blocking Responses**: API returns immediately while processing continues
- **Background Tasks**: Long-running tasks execute asynchronously
- **Proper Cancellation**: Tasks can be cancelled with graceful shutdown

### 5. Semantic Kernel Integration
- **Unified LLM Interface**: Semantic Kernel abstracts Azure OpenAI calls
- **Plugin System**: Agents use SK plugins for tool invocation
- **Prompt Templates**: Reusable prompt templates for consistency
- **Token Management**: Efficient token usage through caching

## Directory Structure

```
azure_multi_agent_chat_bot_poc/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI application entry point
│   │   └── models/
│   │       └── schemas.py       # Pydantic request/response models
│   ├── agents/
│   │   ├── __init__.py
│   │   └── semantic_kernel_agents.py  # Five specialized agents
│   │       ├── BaseSemanticAgent
│   │       ├── GreetingAgent
│   │       ├── ResearcherAgent
│   │       ├── EmailWriterAgent
│   │       ├── DatabaseAgent
│   │       └── EventAndCelebrationAgent
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── semantic_kernel_orchestrator.py  # Main orchestration engine
│   │   │   ├── IntentDetectionService      # LLM-based intent classifier
│   │   │   └── SemanticKernelOrchestrator  # Agent routing and coordination
│   │   └── state.py             # Task state management
│   ├── core/
│   │   ├── __init__.py
│   │   ├── semantic_kernel_factory.py  # SK initialization and kernel creation
│   │   ├── config.py            # Configuration management
│   │   ├── logging_config.py    # Structured logging setup
│   │   ├── cache_service.py     # Caching for responses
│   │   └── exceptions.py        # Custom exception classes
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── cosmos_repository.py # Cosmos DB operations
│   │   └── models.py            # Task and message data models
│   ├── utils/
│   │   ├── __init__.py
│   │   └── upload_employee.py   # Employee data upload utility
│   └── static/
│       └── employees.csv        # Sample employee data
├── main.py                      # Application entry point
├── app.py                       # Alternative app entry point
├── requirements.txt             # Python dependencies (all commented)
├── pyproject.toml               # Python project metadata
├── chat_bot_agent.yml           # Agent configuration
├── workflow.txt                 # Workflow documentation
├── TESTING_GUIDE.md             # Testing instructions
└── README.md                    # This file
```

## Agent Workflows

### Greeting Agent
**Responsibility**: Handle user greetings and conversational interactions

**Workflow**:
1. Receive user message from orchestrator
2. Identify greeting intent (hello, hi, thanks, etc.)
3. Generate warm, contextual greeting response
4. Optionally offer help with other tasks
5. Return response to API

**Capabilities**:
- Multi-language greetings
- Personalized responses
- Context-aware conversation management

### Researcher Agent
**Responsibility**: Perform knowledge-based research and provide information

**Workflow**:
1. Receive research topic from orchestrator
2. Analyze topic using LLM
3. Generate research summary or detailed information
4. Provide citations and references
5. Return research results

**Capabilities**:
- Topic research and summarization
- Knowledge synthesis
- Information aggregation
- Reference generation

### Email Writer Agent
**Responsibility**: Generate professional emails with context

**Workflow**:
1. Receive email requirements (recipient, context, tone)
2. Generate professional email content
3. Format with proper structure and etiquette
4. Provide draft for review
5. Return email content

**Capabilities**:
- Professional tone email generation
- Multiple email types (formal, casual, urgent)
- Template-based email creation
- Custom context integration

### Database Agent
**Responsibility**: Manage CRUD operations on Azure Cosmos DB

**Workflow**:
1. Receive data operation request (create, read, update, delete)
2. Parse operation parameters
3. Execute against Cosmos DB collection
4. Validate operation results
5. Return operation status and data

**Capabilities**:
- CRUD operations on task records
- Query execution
- Data validation
- Transaction management
- Error handling and rollback

### Event and Celebration Agent
**Responsibility**: Create celebration content and manage special occasions

**Workflow**:
1. Receive event details (type, date, participants)
2. Generate celebration or event-specific content
3. Create social media posts or announcements
4. Suggest activities or celebrations
5. Return content and suggestions

**Capabilities**:
- Event post generation
- Celebration content creation
- Social media-ready text
- Special occasion handling
- Personalized celebration suggestions

## API Endpoints

### Chat Message Processing

#### Send Message and Get Response
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "user_id": "user_123",
  "conversation_id": "conv_456"
}

Response: 200 OK
{
  "response": "Hello! I'm doing great. How can I help you today?",
  "intent": "greeting",
  "agent": "GreetingAgent",
  "confidence": 0.95,
  "timestamp": "2024-02-16T10:30:00Z"
}
```

#### Send Research Request
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "Research cloud computing technologies",
  "user_id": "user_123",
  "conversation_id": "conv_456"
}

Response: 200 OK
{
  "response": "Cloud computing refers to the delivery of computing services...",
  "intent": "research",
  "agent": "ResearcherAgent",
  "confidence": 0.92,
  "timestamp": "2024-02-16T10:30:05Z"
}
```

#### Request Email Generation
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "Write a professional email to my manager about the project status",
  "user_id": "user_123",
  "conversation_id": "conv_456"
}

Response: 200 OK
{
  "response": "Dear [Manager Name],\n\nI wanted to provide...",
  "intent": "email",
  "agent": "EmailWriterAgent",
  "confidence": 0.88,
  "timestamp": "2024-02-16T10:30:10Z"
}
```

### Conversation Management

#### Get Conversation History
```http
GET /api/v1/conversations/{conversation_id}

Response: 200 OK
{
  "conversation_id": "conv_456",
  "user_id": "user_123",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-02-16T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help?",
      "agent": "GreetingAgent",
      "timestamp": "2024-02-16T10:00:05Z"
    }
  ]
}
```

#### Clear Conversation
```http
DELETE /api/v1/conversations/{conversation_id}

Response: 204 No Content
```

### Health & Status

#### Health Check
```http
GET /api/health

Response: 200 OK
{
  "status": "healthy",
  "timestamp": "2024-02-16T10:30:00Z",
  "dependencies": {
    "azure_openai": "healthy",
    "cosmos_db": "healthy"
  }
}
```

## Configuration

### Environment Variables

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_API_KEY=<api-key>
AZURE_OPENAI_DEPLOYMENT_NAME=<deployment-name>
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Cosmos DB
COSMOS_DB_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_DB_KEY=<key>
COSMOS_DB_DATABASE_NAME=chat-bot-db
COSMOS_DB_CONTAINER_NAME=messages

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=True

# Logging
LOG_LEVEL=INFO
```

### Configuration Priority

The system uses a configuration hierarchy:
1. Environment variables (highest priority)
2. `.env` file (local development)
3. Default values in `config.py` (lowest priority)

## Getting Started

### Prerequisites

- Python 3.8+
- Azure OpenAI API key and endpoint
- Azure Cosmos DB connection string
- pip package manager

### Installation &amp; Setup

```bash
# Clone repository
git clone <repository-url>
cd azure_multi_agent_chat_bot_poc

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (note: requirements.txt is currently commented)
# Uncomment requirements.txt and run:
# pip install -r requirements.txt

# Or install individual packages:
pip install fastapi uvicorn semantic-kernel langchain-openai azure-cosmos pydantic

# Set up environment variables
cp .env.example .env
# Edit .env with your Azure credentials

# Run the application
python main.py
# or
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Quick Start Example

```bash
# Start the server
uvicorn src.api.main:app --reload

# In another terminal, test the API
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "user_id": "user_123",
    "conversation_id": "conv_456"
  }'
```

### Testing

Refer to [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing instructions.

## Security

### API Security
- Input validation using Pydantic models
- Rate limiting on endpoints
- CORS configuration in FastAPI

### Data Protection
- Sensitive data never logged
- Cosmos DB encryption at rest
- HTTPS recommended for production

### Authentication
For production deployment:
- Implement API key authentication
- Use Azure AD for enterprise deployments
- Store credentials in Azure Key Vault

## Monitoring & Observability

### Structured Logging
All logs include:
- Timestamp (ISO 8601)
- Log level (DEBUG, INFO, WARNING, ERROR)
- Component/agent name
- Contextual data (user_id, conversation_id, etc.)

### Available Logs
- Application logs: `/logs/app.log`
- Agent execution logs: Per-agent debug information
- Error logs: Exception tracking and stack traces

### Key Metrics
- Message processing time
- Agent response time
- Error rate and types
- Intent classification accuracy

## Troubleshooting

### Common Issues

**Issue**: Intent classification not working
- **Cause**: Azure OpenAI endpoint or API key incorrect
- **Solution**: Verify AZURE_OPENAI_* environment variables

**Issue**: Cosmos DB connection fails
- **Cause**: Invalid connection string or network issue
- **Solution**: Check COSMOS_DB_* settings and network connectivity

**Issue**: Agents not responding
- **Cause**: Semantic Kernel not properly initialized
- **Solution**: Check logs, verify all dependencies are installed

**Issue**: High latency in responses
- **Cause**: Slow LLM service or network issues
- **Solution**: Check Azure OpenAI service status, review network

## Project Structure Overview

The codebase is organized following these principles:
- **Separation of Concerns**: Each module has a single responsibility
- **Semantic Kernel-Centric**: All LLM interactions go through Semantic Kernel
- **Async-First**: All I/O operations are asynchronous
- **Stateless API**: All state stored in Cosmos DB

### Key Components

- **Agents** (`src/agents/`): Five specialized agents handling different user intents
- **Orchestrator** (`src/orchestration/`): Intent detection and agent routing
- **API** (`src/api/`): FastAPI application and request/response handling
- **Core** (`src/core/`): Factory, config, logging, and shared utilities
- **Persistence** (`src/persistence/`): Cosmos DB integration and data models

## Contributing

Contributions are welcome! Please ensure:
1. All code follows the existing style and patterns
2. New agents extend `BaseSemanticAgent`
3. Proper error handling is implemented
4. Logging is used appropriately

## License

MIT License

## Support

For questions and issues:
- Review [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing procedures
- Check [workflow.txt](workflow.txt) for system architecture details
- Review logs at level `DEBUG` for detailed execution traces

