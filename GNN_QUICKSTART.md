# Quick Start Guide - Predictive Data Mapping GNN

Get up and running in 5 minutes!

## 🎯 What You'll Build

A fully functional GNN-powered eDiscovery platform with:
- Interactive graph visualization
- AI-powered risk assessment
- Temporal forecasting
- Investigation path finding

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python3 --version

# Check Node.js version (need 18+)
node --version

# Check Docker (optional)
docker --version
```

## 🚀 Three Ways to Start

### Method 1: Automated Script (Easiest)

```bash
# 1. Run setup
./setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Start backend (Terminal 1)
python -m uvicorn gnn_app.api.main:app --reload

# 4. Start frontend (Terminal 2)
cd frontend && npm run dev

# 5. Open browser
open http://localhost:3000
```

### Method 2: Docker (One Command)

```bash
# 1. Configure
cp .env.example .env

# 2. Start everything
docker-compose -f docker-compose.gnn.yml up

# 3. Open browser
open http://localhost:3000
```

### Method 3: Manual (Full Control)

**Backend:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-gnn.txt

# Start server
python -m uvicorn gnn_app.api.main:app --reload
```

**Frontend:**
```bash
# In new terminal
cd frontend

# Install and run
npm install
npm run dev
```

## ✅ Verification

1. **Backend Health Check**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy","version":"1.0.0"}
   ```

2. **Frontend Check**
   - Open http://localhost:3000
   - Should see graph visualization loading

3. **API Docs**
   - Visit http://localhost:8000/docs
   - Interactive API documentation

## 🎮 Your First Actions

### 1. Explore the Dashboard

- **Top Bar**: View system statistics
- **Left Panel**: Adjust filters and controls
- **Center**: Interactive graph visualization
- **Bottom**: Critical files watchlist
- **Right Panel**: Will show node details when selected

### 2. Select a Node

- **Click** any node in the graph
- Right panel shows details
- View risk score, relevance, metadata
- See temporal forecast

### 3. Try Filters

- Move **Min Risk** slider right
- Graph filters to high-risk nodes only
- Enable **Highlight Risk** checkbox
- Nodes color-code by risk level

### 4. Chat with Agent X

- Select a node
- Click **Chat** tab in right panel
- Ask: "What are the risks?"
- Get AI-powered insights

### 5. Find Investigation Path

- Double-click a high-risk node
- System highlights investigation path
- Shows connected high-risk entities

## 🔧 Optional: Set Up Ollama (Local LLM)

For completely local AI without API keys:

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Download model
ollama pull llama3.2

# Verify
curl http://localhost:11434/api/tags
```

Then in the app:
- Go to Chat tab
- Check "Use Local Ollama"
- Chat works 100% offline!

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check Python version
python3 --version  # Must be 3.11+

# Reinstall dependencies
pip install --upgrade -r requirements-gnn.txt

# Check port availability
lsof -i :8000
```

### Frontend build fails

```bash
# Clear cache
cd frontend
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Try again
npm run dev
```

### Graph not loading

1. Check browser console (F12)
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check API proxy in `frontend/vite.config.ts`

### Docker issues

```bash
# Clean everything
docker-compose -f docker-compose.gnn.yml down -v

# Rebuild from scratch
docker-compose -f docker-compose.gnn.yml build --no-cache

# Start again
docker-compose -f docker-compose.gnn.yml up
```

## 📊 Sample Data

The system starts with mock data. To use your own:

### File System Data (CSV)

Create `data/files.csv`:
```csv
file_id,file_name,file_type,owner,created_at,last_accessed,sensitivity
1,contract.pdf,pdf,john.doe,2024-01-15,2024-01-20,high
2,report.docx,docx,jane.smith,2024-02-01,2024-02-05,medium
```

### Email Data (CSV)

Create `data/emails.csv`:
```csv
email_id,sender,recipients,subject,sent_at,has_attachments
1,john@company.com,jane@company.com,Q4 Results,2024-01-15,true
```

### Load Custom Data

```python
from gnn_app.core.data_ingestion import DataIngestionPipeline, FileSystemSource

pipeline = DataIngestionPipeline()
pipeline.add_source(FileSystemSource("data/files.csv"))
graph = pipeline.ingest_all()
```

## 🎯 Next Steps

1. **Read Full Documentation**: See `GNN_README.md`
2. **Explore API**: http://localhost:8000/docs
3. **Customize Filters**: Adjust controls in left panel
4. **Try Advanced Features**: Investigation paths, forecasting
5. **Configure for Production**: See deployment guide

## 💡 Pro Tips

- **Keyboard Shortcuts**:
  - `Esc`: Deselect node
  - Click + drag: Pan graph
  - Scroll: Zoom in/out
  
- **Performance**:
  - Use filters to reduce node count for smoother visualization
  - Enable "Critical Only" for focused analysis

- **AI Chat**:
  - Be specific in questions
  - Reference visible data in graph
  - Try "Summarize the risks" for quick overview

## 📚 Learn More

- **Architecture**: See `docs/architecture.md` (when available)
- **API Reference**: http://localhost:8000/docs
- **Examples**: Check `examples/` directory
- **Video Tutorial**: Coming soon!

## 🆘 Need Help?

- Check logs: 
  - Backend: Terminal where uvicorn is running
  - Frontend: Browser console (F12)
  - Docker: `docker-compose logs -f`

- Common issues: See troubleshooting above
- GitHub Issues: Report bugs
- Community: Join discussions

---

**You're all set!** 🎉 Start exploring the temporal knowledge graph and discover hidden risks in your data.
