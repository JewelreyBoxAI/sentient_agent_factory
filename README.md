# Sentient AI Python Backend

A complete Python backend rewrite of the TypeScript LangChain character.ai-inspired system using LangGraph for distributed memory management and scalable AI character interactions.

## 🚀 Features

- **LangGraph Distributed Memory**: Eliminates singleton pattern issues
- **SQLite Database**: Cost-effective development ($0/month)
- **FAISS Vector Store**: Semantic search for character memories
- **Clerk Authentication**: Compatible with existing frontend
- **Character Agents**: JSON-driven personality traits and moderation
- **Real-time Chat**: WebSocket support for live conversations
- **Rate Limiting**: In-memory protection (no Redis needed)

## 🏗️ Architecture

```
sentient-py-v1/
├── main.py                 # FastAPI application entry point
├── src/
│   ├── config/            # Database and settings configuration
│   ├── models/            # SQLAlchemy database models
│   ├── api/routes/        # FastAPI route handlers
│   ├── services/          # Business logic and external services
│   ├── agents/            # LangGraph character agents
│   └── memory/            # Distributed memory management
├── pyproject.toml         # Poetry dependencies
├── render.yaml           # Render.com deployment config
└── .env                  # Environment variables
```

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- Poetry
- OpenAI API Key
- Clerk credentials (for auth)

### Setup
```bash
cd sentient-py-v1
poetry install
poetry run python init_database.py  # Initialize SQLite database
poetry run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Environment Variables
Copy your credentials to `.env`:
```env
DEBUG=true
DATABASE_URL=sqlite:///./sentient_ai.db
OPENAI_API_KEY=your_openai_api_key_here
CLERK_SECRET_KEY=your_clerk_secret_key_here
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here
CLERK_JWT_ISSUER=https://your-app.clerk.accounts.dev
API_HOST=127.0.0.1
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

## 🌐 Deployment (Render.com)

### Automatic Deployment
1. Push to GitHub repository
2. Connect Render to your GitHub repo
3. Render will automatically detect `render.yaml` and deploy
4. Add environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `CLERK_SECRET_KEY`
   - `CLERK_PUBLISHABLE_KEY`
   - `CLERK_JWT_ISSUER`
   - `ALLOWED_ORIGINS` (include your frontend domain)

### Manual Deployment
```bash
# Build command (Render runs automatically)
pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Start command (Render runs automatically)
poetry run uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 📊 API Endpoints

### Health Check
- `GET /` - Server status and version
- `GET /health` - Health check endpoint

### Companions
- `GET /companions/categories` - List all categories
- `POST /companions/categories` - Create new category
- `GET /companions/` - List user's companions
- `POST /companions/` - Create new companion
- `GET /companions/{id}` - Get specific companion
- `PUT /companions/{id}` - Update companion
- `DELETE /companions/{id}` - Delete companion

### Chat
- `POST /chat/message` - Send message to companion
- `GET /chat/history/{companion_id}` - Get conversation history
- `GET /chat/memory/stats/{companion_id}` - Get memory statistics
- `POST /chat/memory/search` - Semantic search in memories
- `WS /chat/ws/{companion_id}` - WebSocket for real-time chat

### Authentication
- `GET /auth/me` - Get current user info
- `POST /auth/verify` - Verify authentication token

## 🔧 Key Technologies

- **FastAPI**: Modern Python web framework
- **LangGraph**: State-driven agent orchestration
- **LangChain**: LLM integration and prompt management
- **SQLAlchemy**: Database ORM with async support
- **SQLite**: Lightweight database for development
- **FAISS**: Vector similarity search
- **Pydantic**: Data validation and serialization
- **Clerk**: Authentication and user management

## 💰 Cost Structure

- **Database**: $0/month (SQLite)
- **Memory Store**: $0/month (in-memory + FAISS)
- **Hosting**: $0/month (Render free tier)
- **Only cost**: OpenAI API usage (~$0.002 per 1K tokens)

## 🔒 Security Features

- Clerk JWT token validation
- Rate limiting (100 requests per hour per user)
- CORS protection with configurable origins
- Input validation with Pydantic schemas
- SQL injection protection with SQLAlchemy ORM

## 🧪 Testing

```bash
# Run simple import test
poetry run python test_simple.py

# Run comprehensive API tests
poetry run python test_apis.py

# Initialize database with test data
poetry run python init_database.py
```

## 📈 Scaling

The architecture is designed to scale horizontally:
- **Stateless design**: All state in database/vector store
- **Distributed memory**: LangGraph checkpointing
- **Async operations**: Non-blocking I/O
- **Rate limiting**: Prevents abuse
- **Modular structure**: Easy to add new agents/features

## 🔄 Migration from TypeScript

This Python backend is designed to be a drop-in replacement for the TypeScript version with:
- ✅ Same API endpoints and schemas
- ✅ Compatible with existing Clerk authentication
- ✅ Improved memory management (no singleton issues)
- ✅ Better error handling and logging
- ✅ Cost-effective development environment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create GitHub Issues for bugs
- Check the documentation for setup help
- Review the API endpoints for integration guidance 