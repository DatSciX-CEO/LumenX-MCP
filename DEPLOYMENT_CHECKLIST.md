# Deployment Checklist

## 🚀 Pre-Deployment Checklist

### 1. Environment Setup

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Docker and Docker Compose installed (if using Docker)
- [ ] Git repository cloned
- [ ] `.env` file created from `.env.example`

### 2. Configuration

- [ ] Review and update `.env` file:
  ```bash
  # Required
  API_HOST=0.0.0.0
  API_PORT=8000
  
  # Optional - Google ADK
  GOOGLE_API_KEY=your_key_here
  
  # Optional - Ollama
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=llama3.2
  ```

- [ ] Configure GNN model parameters in `.env`:
  ```bash
  GNN_HIDDEN_DIM=128
  GNN_NUM_LAYERS=3
  GNN_AGGREGATION=gcn
  ```

- [ ] Set embedding model (if changing):
  ```bash
  EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
  ```

### 3. Backend Setup

#### Local Development
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-gnn.txt

# Create directories
mkdir -p data models .cache

# Test backend
python -m uvicorn gnn_app.api.main:app --reload
```

- [ ] Virtual environment created
- [ ] Dependencies installed (check for errors)
- [ ] Directories created
- [ ] Backend starts without errors
- [ ] Health check responds: `curl http://localhost:8000/health`

#### Docker
```bash
# Build image
docker build -f Dockerfile.gnn -t gnn-app:latest .

# Test run
docker run -p 8000:8000 gnn-app:latest
```

- [ ] Docker image builds successfully
- [ ] Container runs without errors
- [ ] Health check responds

### 4. Frontend Setup

#### Local Development
```bash
cd frontend

# Install dependencies
npm install

# Configure API URL
echo "VITE_API_URL=http://localhost:8000" > .env

# Test frontend
npm run dev
```

- [ ] Dependencies installed
- [ ] Development server starts
- [ ] Can access at http://localhost:3000
- [ ] No console errors in browser (F12)

#### Production Build
```bash
# Build
npm run build

# Test production build
npm run preview
```

- [ ] Build completes successfully
- [ ] Preview works correctly
- [ ] Static files in `dist/` directory

### 5. Optional Services

#### Ollama (Local LLM)
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.2

# Verify
curl http://localhost:11434/api/tags
```

- [ ] Ollama installed
- [ ] Model downloaded
- [ ] Service responding

#### Redis (Caching)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Test connection
redis-cli ping
```

- [ ] Redis running
- [ ] Connection successful

### 6. Integration Testing

#### Backend Tests
```bash
# Health check
curl http://localhost:8000/health

# Get graph
curl http://localhost:8000/api/graph | jq

# Get stats
curl http://localhost:8000/api/stats | jq

# Test chat (requires node_id from graph)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "use_ollama": true}'
```

- [ ] All endpoints respond
- [ ] No 500 errors
- [ ] Data returned correctly

#### Frontend Tests
- [ ] Open http://localhost:3000
- [ ] Graph loads and displays nodes
- [ ] Click a node - right panel shows details
- [ ] Adjust filters - graph updates
- [ ] Chat tab works (send a message)
- [ ] Critical files panel displays
- [ ] No console errors

#### End-to-End Test
- [ ] Start backend
- [ ] Start frontend
- [ ] Load application
- [ ] Select a node
- [ ] View risk forecast
- [ ] Ask question in chat
- [ ] Flag a node
- [ ] Check critical files
- [ ] Apply filters
- [ ] Refresh data

### 7. Docker Compose Deployment

```bash
# Start all services
docker-compose -f docker-compose.gnn.yml up -d

# Check status
docker-compose -f docker-compose.gnn.yml ps

# View logs
docker-compose -f docker-compose.gnn.yml logs -f

# Test
curl http://localhost:3000
curl http://localhost:8000/health
```

- [ ] All containers running
- [ ] Frontend accessible at port 3000
- [ ] Backend accessible at port 8000
- [ ] No errors in logs

### 8. Production Considerations

#### Security
- [ ] Change default ports if needed
- [ ] Configure CORS properly in `.env`
- [ ] Set up HTTPS with SSL certificates
- [ ] Implement authentication (JWT/OAuth)
- [ ] Rate limiting configured
- [ ] Environment variables secured (not in version control)
- [ ] API keys rotated regularly

#### Performance
- [ ] Enable caching (Redis)
- [ ] Configure resource limits in Docker
- [ ] Set up load balancer for horizontal scaling
- [ ] Enable GPU if available (change `EMBEDDING_DEVICE=cuda`)
- [ ] Monitor memory usage
- [ ] Set up CDN for frontend static files

#### Monitoring
- [ ] Set up logging aggregation (ELK stack)
- [ ] Configure metrics collection (Prometheus)
- [ ] Create dashboards (Grafana)
- [ ] Set up alerts for errors/downtime
- [ ] Monitor API response times
- [ ] Track GNN inference performance

#### Backup & Recovery
- [ ] Regular backups of data directory
- [ ] Model checkpoints saved
- [ ] Database backups (if added)
- [ ] Disaster recovery plan documented
- [ ] Test restore procedures

### 9. Documentation Review

- [ ] README.md reviewed and updated
- [ ] QUICKSTART.md tested and accurate
- [ ] ARCHITECTURE.md reflects current state
- [ ] API documentation auto-generated at /docs
- [ ] Environment variables documented
- [ ] Deployment guide created

### 10. Final Checks

#### Functionality
- [ ] All 9 API endpoints working
- [ ] Graph visualization rendering correctly
- [ ] Filters working as expected
- [ ] Node selection and details display
- [ ] Chat assistant responding
- [ ] Risk forecasting functioning
- [ ] Investigation paths displaying
- [ ] Critical files panel populated

#### Performance
- [ ] Page load time < 5 seconds
- [ ] API response time < 500ms
- [ ] Graph renders with 1000+ nodes
- [ ] No memory leaks in browser
- [ ] Backend memory usage stable

#### Browser Compatibility
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

#### Responsive Design
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (responsive message if not supported)

## 🎉 Ready for Launch!

Once all items are checked, your GNN application is ready for deployment.

## 📊 Post-Deployment

### Day 1
- [ ] Monitor error logs
- [ ] Check API response times
- [ ] Verify all features working
- [ ] Collect user feedback

### Week 1
- [ ] Review performance metrics
- [ ] Analyze usage patterns
- [ ] Identify bottlenecks
- [ ] Plan optimizations

### Month 1
- [ ] Security audit
- [ ] Performance review
- [ ] Feature requests prioritization
- [ ] Roadmap update

## 🆘 Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python3 --version

# Reinstall dependencies
pip install --force-reinstall -r requirements-gnn.txt

# Check port availability
lsof -i :8000

# View logs
tail -f /var/log/gnn-backend.log
```

### Frontend Won't Build
```bash
# Clear cache
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Check Node version
node --version

# View build logs
npm run build --verbose
```

### Docker Issues
```bash
# Stop all
docker-compose -f docker-compose.gnn.yml down

# Remove volumes
docker-compose -f docker-compose.gnn.yml down -v

# Rebuild
docker-compose -f docker-compose.gnn.yml build --no-cache

# Start fresh
docker-compose -f docker-compose.gnn.yml up
```

### Graph Not Loading
1. Check browser console (F12)
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check API proxy in vite.config.ts
4. Verify CORS configuration
5. Check network tab for failed requests

---

## 📞 Support Resources

- **Documentation**: See GNN_README.md
- **API Docs**: http://localhost:8000/docs
- **Architecture**: See GNN_ARCHITECTURE.md
- **Quick Start**: See GNN_QUICKSTART.md

Good luck with your deployment! 🚀
