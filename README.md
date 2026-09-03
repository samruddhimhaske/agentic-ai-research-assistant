# 🤖 AI Research Assistant Agent

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

> A full-stack **Agentic AI** web application that demonstrates the complete agent workflow:  
> **Plan → Select Tools → Execute → Reflect → Generate Answer**

---

## 📋 Table of Contents

- [Project Description](#-project-description)
- [Live Demo](#-live-demo)
- [Features](#-features)
- [Agent Architecture](#-agent-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Environment Setup](#-environment-setup)
- [How to Run Locally](#-how-to-run-locally)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Screenshots](#-screenshots)
- [Deployment](#-deployment)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📖 Project Description

**AI Research Assistant Agent** is a beginner-friendly yet professional demonstration of **Agentic AI** — a system where an AI model doesn't just answer questions, but *plans*, *acts*, *observes*, and *reflects* before delivering a structured response.

Unlike a simple chatbot, this agent:

- **Understands** the user's goal, not just their words
- **Plans** a multi-step research strategy
- **Selects** the right tool for each step (Wikipedia, Calculator, DateTime, Summarizer)
- **Executes** those tools and collects observations
- **Reflects** on whether the gathered information is complete
- **Generates** a clean, structured Markdown answer

This project is ideal for:
- 🎓 College final year projects
- 💼 GitHub portfolio showcasing AI/ML skills
- 📚 Learning how LangChain agents work in practice
- 🗣️ Explaining Agentic AI concepts in interviews or viva

---

## 🌐 Live Demo

| Component | URL |
|-----------|-----|
| Frontend  | [Deploy to Netlify](#deployment) |
| Backend API | [Deploy to Render](#deployment) |
| API Docs  | `http://localhost:8000/docs` (local) |

---

## ✨ Features

### Core Agent Features
- 🧠 **Multi-step reasoning** — breaks complex questions into smaller tasks
- 🔄 **Agentic loop** — Plan → Act → Observe → Reflect → Answer
- 🔧 **4 built-in tools** — Calculator, Wikipedia Search, DateTime, Text Summarizer
- 🪞 **Reflection layer** — agent assesses its own answer quality
- 📋 **Transparent planning** — shows the research plan it created

### Frontend Features
- 🎨 **Professional AI dashboard** — dark/light theme toggle
- 📊 **7-step workflow visualizer** — animated step-by-step progress
- 📝 **Markdown rendering** — structured headings, bullets, bold text
- 🕐 **Query history** — stores and displays previous runs
- 📋 **Copy answer button** — one-click copy to clipboard
- 📱 **Fully responsive** — works on mobile, tablet, and desktop

### Developer Features
- 🔒 **Secure calculator** — AST-based evaluator (no `eval()` security risk)
- 🧪 **Test suite** — tool unit tests + API endpoint tests
- 🐳 **Docker ready** — single command to containerize
- 📦 **Clean architecture** — each component has one clear responsibility
- 📖 **Heavily commented** — every file explains what it does and why

---

## 🏗️ Agent Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│         Orchestrator            │  ← Coordinates all agents
│   (agent/orchestrator.py)       │
└─────────┬───────────────────────┘
          │
    ┌─────▼──────┐
    │  PLANNER   │  Step 1: Read query → create research plan
    │  AGENT     │         (Which tools? In what order?)
    └─────┬──────┘
          │  plan[]
    ┌─────▼──────┐
    │  EXECUTOR  │  Step 2: Execute each plan step using tools
    │  AGENT     │
    └──┬────┬────┘
       │    │  Tools Available:
  ┌────┘    └──────────────────────┐
  │  ┌────────────┐  ┌──────────┐  │
  │  │ Wikipedia  │  │Calculator│  │
  │  │  Search    │  │  Tool    │  │
  │  └────────────┘  └──────────┘  │
  │  ┌────────────┐  ┌──────────┐  │
  │  │  DateTime  │  │Summarizer│  │
  │  │   Tool     │  │  Tool    │  │
  │  └────────────┘  └──────────┘  │
  └────────────────────────────────┘
          │  observations[]
    ┌─────▼──────┐
    │ REFLECTION │  Step 3: Is the gathered info complete?
    │   AGENT    │         Quality assessment
    └─────┬──────┘
          │  reflection text
    ┌─────▼──────┐
    │  RESPONSE  │  Step 4: Write structured Markdown answer
    │ GENERATOR  │
    └─────┬──────┘
          │
    ┌─────▼──────────────────────┐
    │      Final Answer          │  Headings + Bullets + Summary
    │   (Markdown formatted)     │
    └────────────────────────────┘
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| **Planner Agent** | `agent/planner.py` | Analyze query, create step-by-step research plan |
| **Executor Agent** | `agent/executor.py` | Select tools, execute them, collect observations |
| **Reflection Agent** | `agent/reflection.py` | Assess completeness and quality of gathered info |
| **Response Generator** | `agent/response_generator.py` | Write final structured Markdown answer |
| **Orchestrator** | `agent/orchestrator.py` | Coordinate all agents in correct order |

### Available Tools

| Tool | File | Use Case |
|------|------|----------|
| 🔢 **Calculator** | `tools/calculator.py` | Safe math — `sqrt(144)`, `2**10`, `15 * 240 / 100` |
| 🔍 **Wikipedia Search** | `tools/search.py` | General knowledge lookup via Wikipedia API |
| 📅 **DateTime** | `tools/datetime_tool.py` | Current date, time, day of week, UTC |
| 📝 **Text Summarizer** | `tools/summarizer.py` | Extractive summarization of long text |

---

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.111 | REST API framework |
| LangChain | 0.2 | LLM orchestration |
| LangChain-OpenAI | 0.1 | OpenAI model integration |
| Pydantic | 2.7 | Data validation and schemas |
| pydantic-settings | 2.3 | Environment variable loading |
| Wikipedia | 1.4 | Wikipedia search API |
| Uvicorn | 0.30 | ASGI server |

### Frontend
| Technology | Purpose |
|------------|---------|
| HTML5 | Structure |
| CSS3 (Custom Properties) | Styling, dark/light theme |
| Vanilla JavaScript (ES6+) | Interactivity, API calls |
| Marked.js (CDN) | Markdown → HTML rendering |
| Google Fonts (Inter + JetBrains Mono) | Typography |

### Deployment
| Platform | What it hosts |
|----------|--------------|
| Render / Railway | Backend (FastAPI) |
| Netlify / Vercel | Frontend (HTML/CSS/JS) |
| Docker Hub | Container image |

---

## 📁 Project Structure

```
agentic-ai-research-assistant/
│
├── 📂 backend/                    # Python FastAPI backend
│   ├── main.py                    # App entry point + all API endpoints
│   ├── config.py                  # Settings from .env file
│   ├── requirements.txt           # Python dependencies
│   │
│   ├── 📂 agent/                  # 🧠 The AI agent components
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # Coordinates all 4 agents
│   │   ├── planner.py             # Step 1: Creates research plan
│   │   ├── executor.py            # Step 2: Runs tools
│   │   ├── reflection.py          # Step 3: Assesses completeness
│   │   └── response_generator.py  # Step 4: Writes final answer
│   │
│   ├── 📂 tools/                  # 🔧 Agent tools
│   │   ├── __init__.py
│   │   ├── tool_registry.py       # Central tool directory
│   │   ├── calculator.py          # Safe math evaluator
│   │   ├── search.py              # Wikipedia search
│   │   ├── datetime_tool.py       # Date and time info
│   │   └── summarizer.py          # Text summarization
│   │
│   ├── 📂 models/                 # 📦 Pydantic data models
│   │   ├── __init__.py
│   │   └── schemas.py             # Request/response shapes
│   │
│   └── 📂 services/               # 🔌 Business logic services
│       ├── __init__.py
│       └── history_service.py     # In-memory query history
│
├── 📂 frontend/                   # HTML/CSS/JS frontend
│   ├── index.html                 # Main page + agent dashboard
│   ├── style.css                  # Dark/light theme + animations
│   ├── script.js                  # API calls + UI updates
│   └── netlify.toml               # Netlify deployment config
│
├── 📂 tests/                      # Test suite
│   └── test_api.py                # API + tool unit tests
│
├── .env.example                   # Template for environment variables
├── .gitignore                     # Files to exclude from Git
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Multi-container setup
├── Procfile                       # Render/Heroku process config
├── render.yaml                    # Render deployment config
├── LICENSE                        # MIT License
└── README.md                      # This file
```

---

## ⚙️ Installation & Setup

### Prerequisites

Make sure you have these installed before starting:

- **Python 3.11+** — [Download here](https://python.org/downloads)
- **pip** — comes with Python
- **Git** — [Download here](https://git-scm.com)
- **OpenAI API Key** — [Get one here](https://platform.openai.com/api-keys)

Check your versions:
```bash
python --version    # Should show 3.11+
pip --version
git --version
```

---

## 🔐 Environment Setup

**This is the most important step.** Without your API key, the agent can't run.

### Step 1: Copy the example environment file

```bash
# Navigate to the project root
cd agentic-ai-research-assistant

# Copy the example file to create your real .env file
cp .env.example .env
```

### Step 2: Edit the .env file and add your API key

Open `.env` in any text editor:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
MODEL_NAME=gpt-4o-mini
DEBUG=True
APP_HOST=0.0.0.0
APP_PORT=8000
ALLOWED_ORIGINS=*
MAX_ITERATIONS=5
MAX_HISTORY_SIZE=50
```

> ⚠️ **IMPORTANT:** Never commit your `.env` file to GitHub.  
> The `.gitignore` already excludes it, but double-check before pushing.

### Where to get your OpenAI API Key:
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign in or create an account
3. Click your profile → **API keys**
4. Click **"Create new secret key"**
5. Copy it immediately (you can't see it again!)
6. Paste it into your `.env` file

> 💡 **Cost:** `gpt-4o-mini` costs approximately **$0.15 per 1M input tokens**.  
> A typical agent run costs less than **$0.01**. Very affordable for a project!

---

## 🚀 How to Run Locally

### Option A: Run Directly with Python (Recommended for beginners)

```bash
# 1. Navigate to the project root
cd agentic-ai-research-assistant

# 2. Create a Python virtual environment
#    (keeps project packages separate from system Python)
python -m venv venv

# 3. Activate the virtual environment
#    On macOS / Linux:
source venv/bin/activate
#    On Windows:
venv\Scripts\activate

# 4. Install all Python dependencies
pip install -r backend/requirements.txt

# 5. Make sure your .env file has your API key (see above)

# 6. Start the backend server
cd backend
uvicorn main:app --reload --port 8000

# You should see:
# ✓ AI Research Assistant Agent Starting...
# ✓ Uvicorn running on http://0.0.0.0:8000
```

Now open the frontend:
```bash
# In a new terminal, just open the HTML file directly:
# macOS:
open ../frontend/index.html

# Or navigate to frontend/ and open index.html in your browser
```

### Option B: Run with Docker

```bash
# Make sure Docker is installed and running
docker --version

# Build and start the container
docker-compose up --build

# Backend runs at: http://localhost:8000
```

### Verify it's working

```bash
# Test the health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","message":"AI Research Assistant Agent is running","version":"1.0.0","model":"gpt-4o-mini"}
```

Then open your browser to:
- **Frontend:** `frontend/index.html` (open as file)
- **API Docs:** `http://localhost:8000/docs`
- **Health:** `http://localhost:8000/health`

---

## 📡 API Documentation

FastAPI automatically generates interactive documentation at `http://localhost:8000/docs`.

### Endpoints

#### `POST /api/agent/run`
Run the AI agent with a user query.

**Request:**
```json
{
  "query": "What is quantum computing and how fast are quantum computers?",
  "session_id": "optional-string"
}
```

**Response:**
```json
{
  "query": "What is quantum computing...",
  "plan": [
    {
      "step_number": 1,
      "description": "Search Wikipedia for quantum computing",
      "tool_suggested": "WikipediaSearch",
      "completed": true
    }
  ],
  "tools_used": [
    {
      "tool_name": "WikipediaSearch",
      "tool_input": "quantum computing",
      "tool_output": "📚 Wikipedia: Quantum computing...",
      "success": true
    }
  ],
  "observations": ["[WikipediaSearch]: Quantum computing is..."],
  "reflection": "The gathered information fully answers the question.",
  "final_answer": "# What is Quantum Computing?\n\n...",
  "steps": [...],
  "processing_time": "8.3s",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/history`
Get the list of previous queries.

**Query parameters:**
- `limit` (optional, default: 20, max: 50)

**Response:**
```json
{
  "history": [
    {
      "id": "abc12345",
      "query": "What is quantum computing?",
      "answer_preview": "Quantum computing is a type of...",
      "tools_used": ["WikipediaSearch", "TextSummarizer"],
      "timestamp": "2024-01-15T10:30:00",
      "processing_time": "8.3s"
    }
  ],
  "total_count": 1
}
```

#### `GET /health`
Check if the server is running.

```json
{
  "status": "ok",
  "message": "AI Research Assistant Agent is running",
  "version": "1.0.0",
  "model": "gpt-4o-mini"
}
```

#### `GET /api/tools`
List all available agent tools.

---

## 🧪 Testing

```bash
# Navigate to the backend directory
cd backend

# Install test dependencies
pip install pytest httpx

# Run all tests
pytest ../tests/test_api.py -v

# Run specific tests
pytest ../tests/test_api.py::test_health_check -v
pytest ../tests/test_api.py::test_calculator_tool -v

# Run tests without API key (no LLM needed)
pytest ../tests/test_api.py -v -k "not agent_run"
```

**Tests included:**
- ✅ Health endpoint returns 200
- ✅ Root endpoint accessible
- ✅ Tools listing returns 4 tools
- ✅ History returns correct structure
- ✅ Empty/whitespace/short queries rejected
- ✅ Calculator handles valid and invalid expressions
- ✅ DateTime returns current date info
- ✅ Summarizer reduces text length
- ✅ Tool registry finds and runs tools correctly

---

## 📸 Screenshots

> Add your screenshots here after running the project.

| Home Page | Agent Dashboard | Final Answer |
|-----------|----------------|--------------|
| *(screenshot)* | *(screenshot)* | *(screenshot)* |

**To add screenshots:**
1. Run the project locally
2. Take screenshots of key UI states
3. Save them to a `docs/screenshots/` folder
4. Replace the placeholder text above with: `![Home](docs/screenshots/home.png)`

---

## 🚢 Deployment

### Deploy Backend to Render (Free Tier)

1. Push your code to GitHub (see Git section below)
2. Go to [render.com](https://render.com) → Sign up free
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repository
5. Render auto-detects `render.yaml`
6. In the **Environment** tab, add:
   - `OPENAI_API_KEY` = your actual API key
   - `DEBUG` = `False`
7. Click **"Create Web Service"**
8. Wait ~3 minutes for the first deploy
9. Copy your Render URL (e.g. `https://my-agent.onrender.com`)

### Deploy Frontend to Netlify (Free Tier)

1. Go to [netlify.com](https://netlify.com) → Sign up free
2. Click **"Add new site"** → **"Import an existing project"**
3. Connect your GitHub repo
4. Set **Publish directory** to: `frontend`
5. Click **"Deploy site"**
6. Once deployed, **update `API_BASE_URL` in `frontend/script.js`**:
   ```javascript
   // Change this line:
   const API_BASE_URL = "http://localhost:8000";
   // To your Render URL:
   const API_BASE_URL = "https://your-app.onrender.com";
   ```
7. Commit and push — Netlify auto-redeploys!

### Deploy with Docker

```bash
# Build the image
docker build -t ai-research-agent .

# Run the container
docker run -p 8000:8000 --env-file .env ai-research-agent

# Or use docker-compose
docker-compose up --build
```

---

## 🔧 How to Push to GitHub

```bash
# 1. Initialize git in your project folder
cd agentic-ai-research-assistant
git init

# 2. Add all files (the .gitignore keeps secrets out)
git add .

# 3. Verify .env is NOT being tracked
git status    # Should NOT show .env in the list

# 4. Make your first commit
git commit -m "feat: initial commit - AI Research Assistant Agent"

# 5. Create a new repository on GitHub.com
#    Go to github.com → New → Create repository (don't initialize it)

# 6. Add GitHub as the remote
git remote add origin https://github.com/YOUR_USERNAME/ai-research-agent.git

# 7. Push your code
git branch -M main
git push -u origin main
```

---

## 🔮 Future Improvements

Here are ideas for extending this project:

| Feature | Description | Difficulty |
|---------|-------------|------------|
| 🗄️ **Database** | Replace in-memory history with SQLite or PostgreSQL | Beginner |
| 🌐 **Web Search** | Add DuckDuckGo or Tavily search for real-time web results | Beginner |
| 🔁 **Multi-turn** | Remember previous messages in a conversation | Intermediate |
| 📄 **PDF Upload** | Let users upload documents for the agent to analyze | Intermediate |
| 🗂️ **Agent Memory** | Vector database (Chroma/Pinecone) for long-term memory | Intermediate |
| 🤝 **Multi-agent** | Multiple specialized agents collaborating on complex tasks | Advanced |
| 📊 **Analytics** | Dashboard showing agent performance metrics | Intermediate |
| 🔐 **Auth** | User accounts with personal history | Intermediate |
| 🔧 **Custom Tools** | UI for users to add their own tools | Advanced |
| 🌍 **Multilingual** | Support queries in multiple languages | Intermediate |

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/add-web-search`
3. Make your changes with clear comments
4. Test your changes: `pytest tests/test_api.py -v`
5. Commit: `git commit -m "feat: add DuckDuckGo web search tool"`
6. Push: `git push origin feature/add-web-search`
7. Open a Pull Request on GitHub

**Please follow these guidelines:**
- Keep code beginner-friendly with comments
- One feature per PR
- Update README if you add new features or tools

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Feel free to use it for college projects, portfolios, or learning — just give credit! 🙏

---

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com) — incredible Python web framework
- [LangChain](https://langchain.com) — making LLM apps accessible
- [OpenAI](https://openai.com) — the underlying language model
- [Wikipedia](https://wikipedia.org) — free knowledge for the search tool
- [Marked.js](https://marked.js.org) — Markdown rendering in the browser

---

<div align="center">
  <strong>Built with ❤️ for learning Agentic AI</strong><br/>
  <sub>⭐ Star this repo if you found it helpful!</sub>
</div>
