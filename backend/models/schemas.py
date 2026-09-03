"""
models/schemas.py - Data Models (Shapes)
==========================================
Pydantic models define the EXACT structure of data your API accepts and returns.
Think of them as blueprints or contracts:
  - What fields are required?
  - What type should each field be? (string, int, list, etc.)
  - What's the default value if a field is missing?

FastAPI uses these models to:
  1. Automatically validate incoming requests
  2. Automatically generate API documentation
  3. Serialize response data to JSON

If the data doesn't match the model, FastAPI returns a clear error message automatically.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============================================================
# REQUEST MODELS (data coming IN to the API)
# ============================================================

class AgentRequest(BaseModel):
    """
    The data a user sends when asking the agent a question.
    
    Example JSON the frontend sends:
    {
        "query": "What is quantum computing?",
        "session_id": "abc123"
    }
    """
    query: str = Field(
        ...,  # '...' means this field is REQUIRED — cannot be empty
        min_length=3,
        max_length=1000,
        description="The user's question or research topic",
        example="What is quantum computing and how does it work?"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID to group related queries"
    )


# ============================================================
# COMPONENT MODELS (internal agent data structures)
# ============================================================

class AgentStep(BaseModel):
    """
    Represents one step in the agent's thinking process.
    
    The agent goes through multiple steps:
    Step 1: Understanding → Step 2: Planning → Step 3: Tools → etc.
    Each step is stored as an AgentStep object.
    """
    step_number: int = Field(description="Which step this is (1, 2, 3...)")
    step_name: str = Field(description="Short name like 'Understanding Query'")
    status: str = Field(
        default="pending",
        description="Current status: pending, in_progress, completed, failed"
    )
    # User-friendly summary shown on the dashboard (NOT raw AI output)
    summary: str = Field(
        default="",
        description="Safe, user-friendly description of what happened"
    )
    # How long this step took (e.g. "0.8s")
    duration: Optional[str] = Field(
        default=None,
        description="Time taken to complete this step"
    )


class ToolUsage(BaseModel):
    """
    Records which tool was used and what happened.
    
    Example: The agent used the Calculator tool to solve "2 + 2"
    and got back "4".
    """
    tool_name: str = Field(description="Name of the tool (e.g. 'Calculator')")
    tool_input: str = Field(description="What was passed to the tool")
    tool_output: str = Field(description="What the tool returned")
    success: bool = Field(default=True, description="Did the tool run without errors?")


class PlanStep(BaseModel):
    """
    One step inside the agent's research plan.
    
    When the planner breaks down a query, each sub-task becomes a PlanStep.
    Example plan for "What is quantum computing?":
      Step 1: Search Wikipedia for quantum computing basics
      Step 2: Find key concepts and terms
      Step 3: Summarize findings
    """
    step_number: int = Field(description="Order of this step in the plan")
    description: str = Field(description="What needs to be done in this step")
    tool_suggested: Optional[str] = Field(
        default=None,
        description="Which tool might be needed (optional suggestion)"
    )
    completed: bool = Field(
        default=False,
        description="Has this plan step been completed?"
    )


# ============================================================
# RESPONSE MODELS (data going OUT from the API)
# ============================================================

class AgentResponse(BaseModel):
    """
    The complete response the API sends back after running the agent.
    
    This is what the frontend receives and displays to the user.
    Contains everything: the plan, tools used, observations, and final answer.
    
    Example structure:
    {
        "query": "What is AI?",
        "plan": [...],
        "tools_used": [...],
        "observations": [...],
        "reflection": "The gathered information fully answers the question.",
        "final_answer": "# What is AI?\n\nArtificial Intelligence is...",
        "steps": [...],
        "processing_time": "3.2s",
        "timestamp": "2024-01-15T10:30:00"
    }
    """
    query: str = Field(description="The original user question")

    # The agent's step-by-step plan
    plan: list[PlanStep] = Field(
        default=[],
        description="The research plan the agent created"
    )

    # Which tools were used and their results
    tools_used: list[ToolUsage] = Field(
        default=[],
        description="All tools the agent used during research"
    )

    # Raw observations collected from tools
    observations: list[str] = Field(
        default=[],
        description="Information gathered from tools"
    )

    # The reflection agent's assessment
    reflection: str = Field(
        default="",
        description="Agent's assessment of whether the answer is complete"
    )

    # The final answer shown to the user (Markdown formatted)
    final_answer: str = Field(
        description="The structured final answer in Markdown format"
    )

    # Workflow step statuses for the dashboard
    steps: list[AgentStep] = Field(
        default=[],
        description="Status of each workflow step for the UI dashboard"
    )

    # Metadata
    processing_time: str = Field(
        default="",
        description="Total time the agent took to respond"
    )
    timestamp: str = Field(
        default="",
        description="When this response was generated"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier if provided"
    )


class HistoryItem(BaseModel):
    """
    A single entry in the agent's query history.
    Stored in memory and returned by GET /api/history.
    """
    id: str = Field(description="Unique identifier for this history entry")
    query: str = Field(description="The user's original question")
    # Short preview of the answer (first 200 chars)
    answer_preview: str = Field(description="First few words of the answer")
    tools_used: list[str] = Field(
        default=[],
        description="Names of tools that were used"
    )
    timestamp: str = Field(description="When this query was run")
    processing_time: str = Field(
        default="",
        description="How long the agent took"
    )


class HistoryResponse(BaseModel):
    """
    The response for GET /api/history
    Returns a list of previous agent interactions.
    """
    history: list[HistoryItem] = Field(
        description="List of previous queries, newest first"
    )
    total_count: int = Field(description="Total number of history entries")


class HealthResponse(BaseModel):
    """
    Response for GET /health — confirms the server is running.
    Used by deployment platforms to check if the app is alive.
    """
    status: str = Field(default="ok", description="Server health status")
    message: str = Field(
        default="AI Research Assistant Agent is running",
        description="Human-readable status message"
    )
    version: str = Field(default="1.0.0", description="App version")
    model: str = Field(description="Which AI model is configured")


class ErrorResponse(BaseModel):
    """
    Standardized error response format.
    When something goes wrong, the API always returns this shape
    so the frontend knows exactly how to handle errors.
    """
    error: str = Field(description="Short error type label")
    message: str = Field(description="Human-readable explanation of what went wrong")
    detail: Optional[str] = Field(
        default=None,
        description="Technical detail (only shown in debug mode)"
    )
