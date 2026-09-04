"""
AI Research Assistant Agent - FastAPI Application
==================================================

This is the MAIN file of the backend.

It provides:
- FastAPI application
- CORS configuration
- Frontend serving
- Health check
- AI Agent execution
- Query history
- Available tools information
"""

import sys
import os
import time
from pathlib import Path

# Add the backend folder to Python's module search path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

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
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# FRONTEND DIRECTORY
# ============================================================

# Project structure inside Docker:
#
# /app
# ├── backend
# │   ├── main.py
# │   └── ...
# │
# └── frontend
#     ├── index.html
#     ├── style.css
#     └── script.js

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


# ============================================================
# CONFIGURE CORS MIDDLEWARE
# ============================================================

allowed_origins = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================
# STARTUP / SHUTDOWN EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    """
    Runs once when the server starts.
    """
    print("=" * 50)
    print("🚀 AI Research Assistant Agent Starting...")
    print(f"   Model: {settings.model_name}")
    print(f"   Debug: {settings.debug}")
    print(f"   Frontend: {FRONTEND_DIR}")
    print(f"   Docs: http://{settings.app_host}:{settings.app_port}/docs")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs once when the server shuts down.
    """
    print("👋 AI Research Assistant Agent shutting down...")


# ============================================================
# MIDDLEWARE — REQUEST TIMING
# ============================================================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Adds X-Process-Time header to every response.
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
    description="Check if the API server is running correctly.",
)
async def health_check():

    from services.llm_service import get_active_model_name

    return HealthResponse(
        status="ok",
        message="AI Research Assistant Agent is running",
        version="1.0.0",
        model=get_active_model_name(),
    )


# ============================================================
# FRONTEND
# ============================================================

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """
    Serve the AI Research Assistant frontend.
    """

    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Frontend not found",
                "message": "frontend/index.html is missing from the deployment.",
            },
        )

    return FileResponse(index_file)


# ============================================================
# FRONTEND STATIC FILES
# ============================================================

@app.get("/{file_path:path}", include_in_schema=False)
async def serve_frontend_files(file_path: str):
    """
    Serve frontend files such as:

    /style.css
    /script.js
    /images/...
    """

    # Never interfere with API routes
    if file_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    if file_path in ["docs", "redoc", "openapi.json", "health"]:
        raise HTTPException(status_code=404, detail="Not found")

    requested_file = FRONTEND_DIR / file_path

    # Security check: prevent directory traversal
    try:
        requested_file.resolve().relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found")

    if requested_file.is_file():
        return FileResponse(requested_file)

    raise HTTPException(status_code=404, detail="File not found")


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
    4. **Reflect** on gathered information
    5. **Generate** a structured final answer

    Returns the complete workflow result including:

    - Plan
    - Tools used
    - Observations
    - Reflection
    - Final answer
    """,
    responses={
        200: {"description": "Agent successfully processed the query"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    },
)
async def run_agent(request: AgentRequest):
    """
    Run the full Agentic AI workflow.
    """

    # Validate query
    if not request.query or not request.query.strip():

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty. Please enter a question.",
        )

    try:

        # Run full agent workflow
        response = await orchestrator.run(request)

        # Save interaction to history
        try:
            history_service.add_entry(response)
        except Exception:
            # History failure should not break the main request
            pass

        return response

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        error_detail = (
            str(e)
            if settings.debug
            else "An internal error occurred."
        )

        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {error_detail}",
        )


# ============================================================
# HISTORY ENDPOINT
# ============================================================

@app.get(
    "/api/history",
    response_model=HistoryResponse,
    tags=["History"],
    summary="Get Query History",
    description="Retrieve the list of previous agent queries and their results.",
)
async def get_history(limit: int = 20):
    """
    Get previous agent interactions.
    """

    # Keep limit between 1 and 50
    limit = min(limit, 50)
    limit = max(limit, 1)

    history = history_service.get_history(limit=limit)

    total = history_service.get_total_count()

    return HistoryResponse(
        history=history,
        total_count=total,
    )


# ============================================================
# TOOLS INFO ENDPOINT
# ============================================================

@app.get(
    "/api/tools",
    tags=["Agent"],
    summary="List Available Tools",
    description="Get information about all tools the agent can use.",
)
async def get_available_tools():
    """
    Returns metadata about available agent tools.
    """

    from tools.tool_registry import tool_registry

    return {
        "tools": tool_registry.get_tools_metadata(),
        "total_tools": len(tool_registry.get_tool_names()),
        "tool_names": tool_registry.get_tool_names(),
    }


# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Catches unhandled exceptions and returns clean JSON.
    """

    error_message = (
        str(exc)
        if settings.debug
        else "An unexpected error occurred."
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="Something went wrong on the server.",
            detail=error_message if settings.debug else None,
        ).model_dump(),
    )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
