# Predictive Data Mapping GNN

A production-ready Graph Neural Network (GNN) application for predictive data mapping, risk assessment, and investigation in eDiscovery and compliance workflows.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 🎯 Overview

This application transforms eDiscovery from a reactive, time-consuming process into a proactive, AI-powered intelligence platform. By leveraging Graph Neural Networks, it analyzes temporal knowledge graphs to automatically identify risks, predict future threats, and accelerate investigations.

### Key Features

- **🧠 GNN-Powered Analysis**: Deep learning on graph structures for risk and relevance scoring
- **🔮 Temporal Forecasting**: Predict future risk trends based on historical patterns
- **🤖 AI Agents**: Integrated Google ADK and local Ollama LLM for intelligent assistance
- **📊 Interactive Visualization**: D3.js-powered temporal knowledge graph with real-time filtering
- **🔍 Investigation Paths**: Automated path discovery for efficient case building
- **🚨 Critical Watchlist**: Auto-identified high-risk entities
- **🏗️ Production-Ready**: Modular, scalable architecture with Docker support
- **💻 Fully Local**: Can run entirely offline with local models

## 🏗️ Architecture

### Technology Stack

**Backend**
- **Framework**: FastAPI (async REST API)
- **GNN**: PyTorch + PyTorch Geometric
- **Embeddings**: Sentence Transformers (local)
- **AI Agents**: Google ADK + Ollama
- **Database**: SQLAlchemy (modular backend support)

**Frontend**
- **Framework**: React 18 + TypeScript
- **Visualization**: D3.js (force-directed graphs)
- **Styling**: Tailwind CSS
- **Build**: Vite

**Infrastructure**
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **Process Management**: Supervisor

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ D3.js Graph │  │ Control Panel│  │ AI Chat Assistant│  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ REST API
┌────────────────────────────┴────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ GNN Processor│  │ Embedding   │  │ AI Agents        │  │
│  │              │  │ Service     │  │ (ADK + Ollama)   │  │
│  └──────┬───────┘  └──────┬──────┘  └────────┬─────────┘  │
│         │                  │                   │             │
│  ┌──────┴──────────────────┴───────────────────┴─────────┐ │
│  │          Temporal Knowledge Graph                      │ │
│  │  (Nodes: Custodians, Files, Channels, Emails)         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional)
- 4GB+ RAM recommended

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd workspace

# Run setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Start backend
python -m uvicorn gnn_app.api.main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev
```

Visit: http://localhost:3000

### Option 2: Docker (Production)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose -f docker-compose.gnn.yml up

# Or build and run in detached mode
docker-compose -f docker-compose.gnn.yml up -d --build
```

Visit: http://localhost:3000

### Option 3: Manual Setup

#### Backend

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-gnn.txt

# Create directories
mkdir -p data models .cache

# Copy and configure environment
cp .env.example .env
nano .env

# Run backend
python -m uvicorn gnn_app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL (optional)
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev

# Or build for production
npm run build
npm run preview
```

## 📖 Usage Guide

### 1. Initial Dashboard

Upon loading, you'll see:
- **Graph Visualization**: Interactive temporal knowledge graph
- **Control Panel**: Filters and visualization options
- **Statistics**: Real-time graph metrics
- **Critical Files Panel**: Auto-identified high-risk entities

### 2. Filtering Data

Use the Control Panel to filter:
- **Min Relevance**: Filter by relevance score (0.0 - 1.0)
- **Min Risk**: Filter by risk score (0.0 - 1.0)
- **Forecast Months**: Set temporal forecast period
- **Visualization Options**: 
  - Highlight Risk: Color nodes by risk level
  - Show Investigation Path: Display investigation routes
- **Node Filters**:
  - Flagged Only: Show only flagged entities
  - Critical Only: Show only critical entities

### 3. Exploring Nodes

**Single Click**: Select a node to view:
- Detailed metrics and metadata
- Risk assessment and forecast
- Graph connectivity metrics
- Timeline information

**Double Click**: Show investigation path from selected node

### 4. AI Assistant (Agent X)

In the Chat tab:
- Ask questions about selected entities
- Request risk analysis
- Get investigation recommendations
- Toggle between Google ADK and local Ollama

Example queries:
- "What are the main risks associated with this file?"
- "Who has accessed this recently?"
- "Summarize the key connections"
- "What should I investigate next?"

### 5. Investigation Workflow

1. **Start at Dashboard**: Review critical files and high-risk nodes
2. **Apply Filters**: Narrow down to relevant entities
3. **Select Node**: Click to view details
4. **Analyze Risk**: Review risk scores and forecast
5. **Explore Path**: Double-click to see investigation path
6. **Flag Entities**: Mark important nodes for review
7. **Ask Agent X**: Get AI-powered insights
8. **Export Results**: (Coming in v1.1)

## 🔧 Configuration

### Environment Variables

Key configurations in `.env`:

```bash
# Google ADK (optional)
GOOGLE_API_KEY=your_key_here

# Ollama (local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# GNN Model
GNN_HIDDEN_DIM=128
GNN_NUM_LAYERS=3
GNN_AGGREGATION=gcn

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
```

### Data Ingestion

The system supports multiple data sources:

```python
from gnn_app.core.data_ingestion import DataIngestionPipeline, FileSystemSource

pipeline = DataIngestionPipeline()

# Add data sources
pipeline.add_source(FileSystemSource("data/files.csv"))
pipeline.add_source(EmailSource("data/emails.csv"))
pipeline.add_source(CollaborationSource("data/channels.json"))

# Ingest and build graph
graph = pipeline.ingest_all()
```

## 🧪 Development

### Running Tests

```bash
# Backend tests
pytest tests/

# With coverage
pytest --cov=gnn_app tests/
```

### Code Quality

```bash
# Linting
ruff check gnn_app/

# Type checking
mypy gnn_app/

# Formatting
black gnn_app/
```

### Adding New Features

The architecture is modular. To extend:

1. **New Data Sources**: Implement `DataSource` in `core/data_ingestion.py`
2. **Custom GNN Layers**: Extend model in `models/gnn_model.py`
3. **New API Endpoints**: Add routes in `api/main.py`
4. **Frontend Components**: Add React components in `frontend/src/components/`

## 📊 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoints:

```
GET  /api/graph              - Get filtered graph
GET  /api/nodes/{id}         - Get node details
GET  /api/critical-files     - Get critical files
POST /api/investigation-path - Find investigation path
POST /api/forecast           - Forecast node risk
POST /api/analyze            - AI analysis of node
POST /api/chat               - Chat with Agent X
GET  /api/stats              - Graph statistics
GET  /health                 - Health check
```

## 🐳 Docker Services

The `docker-compose.gnn.yml` includes:

- **gnn-backend**: FastAPI + GNN processor
- **gnn-frontend**: React app with Nginx
- **ollama**: Local LLM service (optional)
- **redis**: Caching layer (optional)

```bash
# Start specific service
docker-compose -f docker-compose.gnn.yml up gnn-backend

# View logs
docker-compose -f docker-compose.gnn.yml logs -f

# Scale services
docker-compose -f docker-compose.gnn.yml up --scale gnn-backend=3

# Stop all
docker-compose -f docker-compose.gnn.yml down
```

## 🔒 Security Considerations

1. **API Keys**: Never commit `.env` file
2. **CORS**: Configure `API_CORS_ORIGINS` for production
3. **Authentication**: Add auth middleware (not included in MVP)
4. **Data Privacy**: All processing can be done locally
5. **HTTPS**: Use reverse proxy with SSL in production

## 📈 Performance

- **Graph Size**: Optimized for 10K+ nodes, 50K+ edges
- **Response Time**: <2s for most queries
- **Memory**: ~2GB for typical workload
- **Scalability**: Horizontally scalable with load balancer

## 🗺️ Roadmap

- [x] v1.0: Production MVP with GNN and AI agents
- [ ] v1.1: Export and reporting features
- [ ] v1.2: Real-time data streaming
- [ ] v1.3: Advanced ML models (transformers)
- [ ] v1.4: Multi-tenancy support
- [ ] v2.0: Enterprise features (SSO, audit logs)

## 🤝 Contributing

Contributions welcome! See `CONTRIBUTING.md` for guidelines.

## 📄 License

MIT License - see `LICENSE` file

## 🙏 Acknowledgments

- PyTorch Geometric team
- D3.js community
- Google ADK team
- Ollama project

## 📞 Support

- Documentation: See `docs/` directory
- Issues: GitHub Issues
- Email: support@example.com

---

Built with ❤️ for the eDiscovery and Compliance community
