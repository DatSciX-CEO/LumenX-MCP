# Architecture Documentation

## System Overview

The Predictive Data Mapping GNN application is a production-ready, modular system designed for scalability, maintainability, and flexibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                    (React + TypeScript)                      │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────┴────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  ┌────────────┐  ┌───────────┐  ┌─────────────────────┐   │
│  │ Graph API  │  │ AI Agent  │  │ Forecasting API     │   │
│  └──────┬─────┘  └─────┬─────┘  └──────────┬──────────┘   │
└─────────┼──────────────┼─────────────────────┼──────────────┘
          │              │                     │
┌─────────┴──────────────┴─────────────────────┴──────────────┐
│                     Service Layer                            │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐│
│  │ GNN Processor   │  │ Embedding    │  │ LLM Service    ││
│  │                 │  │ Service      │  │ (Ollama/ADK)   ││
│  └────────┬────────┘  └──────┬───────┘  └────────┬───────┘│
└───────────┼───────────────────┼──────────────────┼─────────┘
            │                   │                  │
┌───────────┴───────────────────┴──────────────────┴─────────┐
│                     Core Layer                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Temporal Knowledge Graph                    │  │
│  │  Nodes: Custodians, Files, Channels, Emails         │  │
│  │  Edges: Relationships & Interactions                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React + TypeScript)

**Location**: `/frontend/src/`

**Architecture Pattern**: Component-based architecture with centralized state management

**Key Components**:

```
frontend/src/
├── components/           # React components
│   ├── GraphVisualization.tsx    # D3.js graph rendering
│   ├── ControlPanel.tsx          # Filters and controls
│   ├── RightSidebar.tsx          # Node details container
│   ├── NodeDetailPanel.tsx       # Node information display
│   ├── ChatAssistant.tsx         # AI chat interface
│   ├── CriticalFilePanel.tsx     # Bottom panel
│   └── Header.tsx                # Top navigation
├── services/            # API communication
│   └── api.ts           # Axios-based API client
├── types/               # TypeScript definitions
│   └── graph.ts         # Graph data structures
├── hooks/               # Custom React hooks
└── App.tsx              # Main application container
```

**State Management**:
- **Pattern**: Props drilling from App.tsx
- **Why**: Simple, predictable, no external dependencies
- **Future**: Can migrate to Redux/Zustand for complex state

**Data Flow**:
1. User interaction triggers event in component
2. Event handler calls API via `services/api.ts`
3. API response updates App.tsx state
4. State flows down via props
5. Components re-render with new data

### 2. Backend API (FastAPI)

**Location**: `/gnn_app/api/`

**Architecture Pattern**: RESTful API with async/await

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/graph` | GET | Retrieve filtered graph |
| `/api/nodes/{id}` | GET | Get node details |
| `/api/critical-files` | GET | Get critical files |
| `/api/investigation-path` | POST | Find investigation path |
| `/api/forecast` | POST | Forecast node risk |
| `/api/analyze` | POST | AI analysis |
| `/api/chat` | POST | Chat with Agent X |
| `/api/stats` | GET | Graph statistics |
| `/health` | GET | Health check |

**Request/Response Flow**:
```
Client Request
    ↓
FastAPI Endpoint
    ↓
Service Layer (GNN Processor, Embedding Service, AI Agents)
    ↓
Core Layer (Temporal Graph)
    ↓
Response to Client
```

### 3. GNN Processing Pipeline

**Location**: `/gnn_app/services/gnn_processor.py`

**Architecture**: Pipeline pattern

**Flow**:
```
1. Data Ingestion
   └── FileSystemSource, EmailSource, CollaborationSource
       └── Parse raw data → Create nodes & edges

2. Graph Construction
   └── TemporalGraph
       └── Nodes (custodians, files, channels)
       └── Edges (relationships with timestamps)

3. Embedding Generation
   └── Sentence Transformers (local)
       └── Convert text → 384-dim vectors

4. GNN Encoding
   └── PyTorch Geometric
       └── Message passing (3 layers)
       └── Node embeddings (128-dim)

5. Prediction
   └── Risk Predictor
   └── Relevance Predictor
   └── Temporal Forecaster

6. Output
   └── Updated graph with scores & embeddings
```

### 4. GNN Model Architecture

**Location**: `/gnn_app/models/gnn_model.py`

**Model Components**:

```python
PredictiveGNN
├── GNNEncoder (3 layers)
│   ├── Input projection (384 → 128)
│   ├── GCNConv/GATConv/SAGEConv layers
│   ├── Batch normalization
│   ├── ReLU activation
│   └── Dropout (0.1)
│
├── RiskPredictor
│   ├── MLP (128 → 64 → 1) for risk score
│   └── MLP (128 → 64 → 4) for risk level
│
├── RelevancePredictor
│   └── MLP (128 → 64 → 1) for relevance
│
└── TemporalForecaster (optional)
    ├── LSTM (2 layers)
    └── MLP for future risk prediction
```

**Message Passing**:
```
For each node v:
    1. Aggregate messages from neighbors: m_v = AGG({h_u | u ∈ N(v)})
    2. Update node representation: h_v' = UPDATE(h_v, m_v)
    3. Apply non-linearity: h_v' = ReLU(BatchNorm(h_v'))
    4. Add residual: h_v'' = h_v' + h_v (skip connection)
```

**Training** (Not included in MVP, would be):
```python
for epoch in range(num_epochs):
    for batch in dataloader:
        # Forward pass
        predictions = model(batch.x, batch.edge_index)
        
        # Compute losses
        risk_loss = F.mse_loss(predictions['risk_scores'], batch.risk_labels)
        relevance_loss = F.mse_loss(predictions['relevance_scores'], batch.relevance_labels)
        
        # Backprop
        loss = risk_loss + relevance_loss
        loss.backward()
        optimizer.step()
```

### 5. AI Agents

**Location**: `/gnn_app/agents/`

**Two Agent Types**:

**Google ADK Agent** (`google_adk_agent.py`):
```python
GoogleADKAgent
├── Uses Gemini models
├── Features:
│   ├── analyze_node(): Detailed node analysis
│   ├── suggest_investigation_path(): Path recommendations
│   └── answer_query(): Natural language Q&A
└── Context-aware prompts with graph data
```

**Ollama Agent** (`services/llm_service.py`):
```python
OllamaService
├── Local LLM (Llama 3.2, Mistral, etc.)
├── Fully offline capability
├── Features:
│   ├── analyze_node(): Node analysis
│   ├── answer_query(): Q&A
│   └── chat(): Conversational interface
└── HTTP API to local Ollama server
```

**Agent Selection**:
```python
# In API
if use_ollama or not google_adk_available:
    response = await ollama_service.answer_query(query, node)
else:
    response = google_adk_agent.answer_query(query, node)
```

### 6. Data Ingestion

**Location**: `/gnn_app/core/data_ingestion.py`

**Pattern**: Strategy pattern with abstract DataSource

**Sources**:

```python
DataSource (Abstract)
├── FileSystemSource
│   ├── Input: files.csv
│   └── Creates: File nodes, Custodian nodes, Access edges
├── EmailSource
│   ├── Input: emails.csv
│   └── Creates: Email nodes, Custodian nodes, Sent/Received edges
└── CollaborationSource
    ├── Input: channels.json
    └── Creates: Channel nodes, Custodian nodes, Membership edges
```

**Pipeline**:
```python
pipeline = DataIngestionPipeline()
pipeline.add_source(FileSystemSource("data/files.csv"))
pipeline.add_source(EmailSource("data/emails.csv"))
pipeline.add_source(CollaborationSource("data/channels.json"))
graph = pipeline.ingest_all()  # Merges all sources
```

### 7. Graph Data Model

**Location**: `/gnn_app/core/graph_schema.py`

**Core Classes**:

```python
GraphNode
├── id: str (unique identifier)
├── type: NodeType (custodian|file|channel|email)
├── label: str (display name)
├── metadata: dict (type-specific data)
├── timestamps: created_at, updated_at, last_accessed
├── GNN outputs:
│   ├── embedding: List[float]
│   ├── relevance_score: float (0-1)
│   ├── risk_score: float (0-1)
│   ├── risk_level: RiskLevel (low|medium|high|critical)
│   └── forecasted_risk: Optional[float]
├── Graph metrics:
│   ├── degree: int
│   ├── in_degree: int
│   └── out_degree: int
└── Investigation:
    ├── is_flagged: bool
    ├── is_critical: bool
    └── investigation_notes: List[str]

GraphEdge
├── id: str
├── source_id: str
├── target_id: str
├── edge_type: EdgeType (sent_email|accessed_file|...)
├── timestamp: datetime
├── weight: float
├── confidence: float
├── is_anomalous: bool
└── risk_contribution: float

TemporalGraph
├── nodes: Dict[str, GraphNode]
├── edges: List[GraphEdge]
├── metadata: timestamps, counts
└── Methods:
    ├── add_node()
    ├── add_edge()
    ├── get_node_neighbors()
    ├── get_critical_nodes()
    └── get_nodes_by_type()
```

## Deployment Architecture

### Development

```
┌─────────────┐         ┌─────────────┐
│   Frontend  │         │   Backend   │
│   (Vite)    │────────▶│  (Uvicorn)  │
│  Port 3000  │ Proxy   │  Port 8000  │
└─────────────┘         └─────────────┘
```

### Production (Docker)

```
┌──────────────────────────────────────────┐
│            Docker Compose                │
│  ┌────────────┐  ┌──────────────────┐   │
│  │  Frontend  │  │     Backend      │   │
│  │  (Nginx)   │  │    (FastAPI)     │   │
│  │  Port 80   │  │    Port 8000     │   │
│  └────────────┘  └──────────────────┘   │
│        │               │                 │
│        └───────┬───────┘                 │
│                │                         │
│  ┌─────────────┴──────────────────┐     │
│  │       Ollama (Optional)         │     │
│  │       Port 11434                │     │
│  └─────────────────────────────────┘     │
└──────────────────────────────────────────┘
```

### Production (Kubernetes) - Future

```
┌─────────────────────────────────────────┐
│              Ingress                     │
│         (Load Balancer)                  │
└────────────┬───────────────┬────────────┘
             │               │
   ┌─────────┴────┐    ┌────┴─────────┐
   │   Frontend   │    │   Backend    │
   │   (Pod)      │    │   (Pod x3)   │
   └──────────────┘    └──────────────┘
                             │
                       ┌─────┴─────┐
                       │   Redis   │
                       │  (Cache)  │
                       └───────────┘
```

## Design Patterns Used

1. **Strategy Pattern**: Data sources (FileSystemSource, EmailSource)
2. **Factory Pattern**: Model creation (`create_model()`)
3. **Singleton Pattern**: Service instances (`get_gnn_processor()`)
4. **Pipeline Pattern**: Data ingestion flow
5. **Observer Pattern**: D3.js force simulation updates
6. **Component Pattern**: React UI components

## Scalability Considerations

### Horizontal Scaling
- **Backend**: Stateless API, can run multiple instances behind load balancer
- **Frontend**: Static files, can be served by CDN
- **Processing**: Async tasks can be moved to Celery workers

### Vertical Scaling
- **GNN**: Can move to GPU for larger graphs (change `device='cuda'`)
- **Embeddings**: Batch processing with larger batch sizes
- **Memory**: Graph partitioning for very large datasets

### Caching Strategy
```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
   ┌───▼────┐ Cache Hit
   │ Redis  │───────────┐
   └───┬────┘           │
       │ Cache Miss     │
       │                │
   ┌───▼────────┐   ┌───▼────────┐
   │ GNN Process│   │  Response  │
   └────────────┘   └────────────┘
```

## Security Architecture

### Authentication (To be added)
```
Request → JWT Middleware → Validate Token → Allow/Deny
```

### Data Privacy
- All processing local by default
- Optional cloud AI (user controlled)
- No data sent externally without explicit configuration

### API Security
- CORS configuration
- Rate limiting (future)
- Input validation (Pydantic models)

## Monitoring & Observability

### Logging
```python
import structlog
logger = structlog.get_logger()
logger.info("event", key=value, ...)
```

### Metrics (Future)
- Prometheus metrics endpoint
- Grafana dashboards
- Request latency, throughput, error rates

### Health Checks
```
GET /health
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-..."
}
```

## Testing Strategy

### Unit Tests
```
tests/
├── test_models_config.py    # Model tests
├── test_data_sources.py      # Data ingestion tests
└── test_server.py            # API tests
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_full_pipeline():
    # Ingest data
    pipeline = DataIngestionPipeline()
    graph = pipeline.create_mock_graph()
    
    # Process
    processor = GNNProcessor()
    graph = processor.process_graph(graph)
    
    # Verify
    assert graph.total_nodes > 0
    assert all(n.risk_score >= 0 for n in graph.nodes.values())
```

## Performance Benchmarks

**Target Performance** (10K nodes, 50K edges):
- Graph loading: <5s
- GNN inference: <2s
- API response: <500ms
- Frontend rendering: <1s
- Memory usage: <2GB

## Future Enhancements

1. **Real-time Updates**: WebSocket for live graph updates
2. **Advanced ML**: Transformer-based models, attention mechanisms
3. **Distributed Processing**: Spark/Dask for massive graphs
4. **Advanced Visualization**: 3D graphs, VR/AR interfaces
5. **Multi-tenancy**: Isolate data per organization
6. **Advanced Analytics**: Anomaly detection, pattern mining

---

This architecture is designed to be:
- **Modular**: Easy to swap components
- **Scalable**: Can grow with data size
- **Maintainable**: Clear separation of concerns
- **Flexible**: Supports multiple deployment scenarios
- **Production-Ready**: Includes monitoring, health checks, and error handling
