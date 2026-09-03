"""
main.py - FastAPI Application Entry Point
==========================================
This is the MAIN file of the backend. It does three things:

1. Creates the FastAPI app with metadata (title, description, version)
2. Configures middleware (CORS so the frontend can talk to it)
3. Defines all API endpoints (routes)

WHAT IS FastAPI?
  FastAPI is a modern Python web framework for building APIs.
  - It's fast (one of the fastest Python frameworks)
  - It auto-generates interactive documentation at /docs
  - It validates request/response data using Pydantic models
  - It's easy to learn and beginner-friendly

API ENDPOINTS:
  POST /api/agent/run   → Run the AI agent with a user query
  GET  /api/history     → Get previous agent runs
  GET  /health          → Check if the server is running

HOW TO RUN THIS FILE:
  uvicorn main:app --reload --port 8000
  
  Then open:
  - API docs: http://localhost:8000/docs
  - Health check: http://localhost:8000/health
"""

import sys
import os

# Add the backend folder to Python's module search path
# This allows imports like: from agent.orchestrator import orchestrator
# Without this, Python wouldn't know where to find our modules
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# Import our modules
from config import settings, get_allowed_origins
from models.schemas import (
    AgentRequest,
    AgentResponse,
    HistoryResponse,
    HealthResponse,
    ErrorResponse,
)
from agent.orchestrator import orchestrator
from services.history_service import history_service

# ============================================================
# CREATE THE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Research Assistant Agent",
    description="""
    ## 🤖 AI Research Assistant Agent API
    
    An intelligent Agentic AI system that:
    - **Plans** research steps for your query
    - **Selects** and executes appropriate tools
    - **Reflects** on gathered information
    - **Generates** a structured, comprehensive answer
    
    ### Agent Workflow
    `Query → Plan → Execute Tools → Reflect → Generate Answer`
    
    ### Available Tools
    - 🔢 **Calculator** — Safe mathematical calculations
    - 🔍 **Wikipedia Search** — General knowledge lookup
    - 📅 **DateTime** — Current date and time info
    - 📝 **Text Summarizer** — Condense long text
    """,
    version="1.0.0",
    # The /docs URL shows interactive Swagger UI
    docs_url="/docs",
    # The /redoc URL shows alternative documentation
    redoc_url="/redoc",
)

# ============================================================
# CONFIGURE CORS MIDDLEWARE
# ============================================================
# CORS = Cross-Origin Resource Sharing
# Without this, a browser would block requests from the frontend
# (which is on a different URL) to the backend.
#
# Example of what CORS solves:
#   Frontend: http://localhost:3000  (or your Netlify URL)
#   Backend:  http://localhost:8000  (or your Render URL)
#   Without CORS: browser blocks the request!
#   With CORS: backend says "I allow requests from that frontend"

allowed_origins = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,        # Which frontends can access this API
    allow_credentials=True,               # Allow cookies/auth headers
    allow_methods=["GET", "POST", "OPTIONS"],  # Allowed HTTP methods
    allow_headers=["*"],                  # Allow all headers
)

# ============================================================
# STARTUP / SHUTDOWN EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    """
    Runs once when the server starts.
    Good place for initialization logic (DB connections, loading models, etc.)
    """
    print("=" * 50)
    print("🚀 AI Research Assistant Agent Starting...")
    print(f"   Model: {settings.model_name}")
    print(f"   Debug: {settings.debug}")
    print(f"   Docs:  http://{settings.app_host}:{settings.app_port}/docs")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Runs once when the server shuts down."""
    print("👋 AI Research Assistant Agent shutting down...")


# ============================================================
# MIDDLEWARE — REQUEST TIMING
# ============================================================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware that adds an X-Process-Time header to every response.
    
    Middleware runs on EVERY request before and after the endpoint handler.
    This one measures how long each request takes.
    
    You can see this header in your browser's Network tab.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = round(time.time() - start_time, 4)
    response.headers["X-Process-Time"] = f"{process_time}s"
    return response


# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health Check",
    description="Check if the API server is running correctly."
)
async def health_check():
    """Health check endpoint."""
    from services.llm_service import get_active_model_name
    return HealthResponse(
        status="ok",
        message="AI Research Assistant Agent is running",
        version="1.0.0",
        model=get_active_model_name()
    )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get(
    "/",
    tags=["System"],
    summary="API Root",
    description="Welcome message and links to documentation."
)
async def root():
    """
    Root endpoint — confirms the API is accessible.
    Redirects users to the interactive documentation.
    """
    return {
        "message": "Welcome to the AI Research Assistant Agent API! 🤖",
        "docs": "/docs",
        "health": "/health",
        "run_agent": "POST /api/agent/run",
        "history": "GET /api/history",
    }


# ============================================================
# MAIN AGENT ENDPOINT
# ============================================================

@app.post(
    "/api/agent/run",
    response_model=AgentResponse,
    tags=["Agent"],
    summary="Run the AI Agent",
    description="""
    Submit a question to the AI Research Assistant Agent.
    
    The agent will:
    1. **Understand** your query
    2. **Plan** the research steps
    3. **Execute** the appropriate tools
    4. **Reflect** on the gathered information
    5. **Generate** a structured final answer
    
    Returns the complete workflow result including the plan,
    tools used, observations, reflection, and final answer.
    """,
    responses={
        200: {"description": "Agent successfully processed the query"},
        400: {"description": "Invalid request (query too short/long)"},
        500: {"description": "Internal server error"},
    }
)
async def run_agent(request: AgentRequest):
    """
    Run the full Agentic AI workflow for a user query.
    
    This is the main endpoint the frontend calls when the user
    clicks "Run Agent".
    
    Request body:
        {
            "query": "What is quantum computing?",
            "session_id": "optional-session-id"
        }
    
    Response:
        Complete AgentResponse with plan, tools, observations,
        reflection, final answer, and workflow step statuses.
    """
    # Validate the query is not empty/whitespace
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty. Please enter a question."
        )

    try:
        # Run the full agent workflow
        # This calls: planner → executor → reflector → response_generator
        response = await orchestrator.run(request)

        # Save this interaction to history
        # (even if the answer isn't perfect, save what we got)
        try:
            history_service.add_entry(response)
        except Exception:
            # Don't fail the main request if history saving fails
            pass

        return response

    except ValueError as e:
        # ValueError usually means bad input data
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Catch-all for unexpected errors
        # In debug mode, show the full error; in production, hide details
        error_detail = str(e) if settings.debug else "An internal error occurred."

        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {error_detail}"
        )


# ============================================================
# HISTORY ENDPOINT
# ============================================================

@app.get(
    "/api/history",
    response_model=HistoryResponse,
    tags=["History"],
    summary="Get Query History",
    description="Retrieve the list of previous agent queries and their results."
)
async def get_history(limit: int = 20):
    """
    Get the history of previous agent interactions.
    
    Returns recent queries and short previews of their answers.
    Results are ordered newest-first.
    
    Query parameters:
        limit: Maximum number of entries to return (default: 20, max: 50)
    
    Returns:
        HistoryResponse with list of HistoryItem objects
    """
    # Cap the limit to prevent requesting too much data
    limit = min(limit, 50)
    limit = max(limit, 1)

    history = history_service.get_history(limit=limit)
    total = history_service.get_total_count()

    return HistoryResponse(
        history=history,
        total_count=total
    )


# ============================================================
# TOOLS INFO ENDPOINT (Bonus)
# ============================================================

@app.get(
    "/api/tools",
    tags=["Agent"],
    summary="List Available Tools",
    description="Get information about all tools the agent can use."
)
async def get_available_tools():
    """
    Returns metadata about all available agent tools.
    
    Useful for the frontend to display which tools are available,
    and for developers to understand the agent's capabilities.
    """
    from tools.tool_registry import tool_registry
    return {
        "tools": tool_registry.get_tools_metadata(),
        "total_tools": len(tool_registry.get_tool_names()),
        "tool_names": tool_registry.get_tool_names()
    }


# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches ANY unhandled exception across the entire app.
    
    Instead of returning a confusing Python traceback to the user,
    this returns a clean JSON error response.
    """
    error_message = str(exc) if settings.debug else "An unexpected error occurred."

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="Something went wrong on the server.",
            detail=error_message if settings.debug else None
        ).model_dump()
    )


# ============================================================
# RUN DIRECTLY (for development)
# ============================================================

if __name__ == "__main__":
    """
    Run the app directly with: python main.py
    
    This is useful for quick testing during development.
    For production, use: uvicorn main:app --host 0.0.0.0 --port 8000
    """
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,  # Auto-reload on file changes in debug mode
        log_level="debug" if settings.debug else "info"
    )
