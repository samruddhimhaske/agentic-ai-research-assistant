"""
tests/test_api.py - API Tests
===============================
Basic tests to verify the API endpoints work correctly.

HOW TO RUN:
  From the project root:
    cd backend
    pip install pytest httpx
    pytest ../tests/test_api.py -v

These tests use FastAPI's TestClient which runs the app
in-process without needing a real server running.

NOTE: The /api/agent/run tests require a valid OPENAI_API_KEY
in your .env file. The other tests work without an API key.
"""

import sys
import os

# Add backend to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from fastapi.testclient import TestClient
from main import app

# Create the test client
client = TestClient(app)


# ============================================================
# HEALTH CHECK TESTS (no API key needed)
# ============================================================

def test_health_check():
    """Test that the health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data
    assert "model" in data
    print(f"✓ Health check passed. Model: {data['model']}")


def test_root_endpoint():
    """Test that the root endpoint is accessible."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    print("✓ Root endpoint accessible")


def test_tools_endpoint():
    """Test that the tools listing endpoint works."""
    response = client.get("/api/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "total_tools" in data
    assert data["total_tools"] == 4  # We have 4 tools
    tool_names = data["tool_names"]
    assert "Calculator" in tool_names
    assert "WikipediaSearch" in tool_names
    assert "DateTime" in tool_names
    assert "TextSummarizer" in tool_names
    print(f"✓ Tools endpoint: {tool_names}")


def test_history_empty():
    """Test that history starts empty and returns correct structure."""
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert "total_count" in data
    assert isinstance(data["history"], list)
    print(f"✓ History endpoint works. Entries: {data['total_count']}")


def test_history_limit_parameter():
    """Test that the limit query parameter works."""
    response = client.get("/api/history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["history"]) <= 5
    print("✓ History limit parameter works")


# ============================================================
# INPUT VALIDATION TESTS (no API key needed)
# ============================================================

def test_agent_empty_query():
    """Test that empty queries are rejected with 400."""
    response = client.post("/api/agent/run", json={"query": ""})
    assert response.status_code == 400
    print("✓ Empty query correctly rejected")


def test_agent_whitespace_query():
    """Test that whitespace-only queries are rejected."""
    response = client.post("/api/agent/run", json={"query": "   "})
    assert response.status_code == 400
    print("✓ Whitespace query correctly rejected")


def test_agent_missing_query():
    """Test that missing query field returns 422 (validation error)."""
    response = client.post("/api/agent/run", json={})
    assert response.status_code == 422  # Pydantic validation error
    print("✓ Missing query field correctly rejected")


def test_agent_query_too_short():
    """Test that very short queries are rejected."""
    response = client.post("/api/agent/run", json={"query": "hi"})
    assert response.status_code == 422  # min_length=3 in Pydantic model
    print("✓ Too-short query correctly rejected")


# ============================================================
# TOOL UNIT TESTS (no API key needed)
# ============================================================

def test_calculator_tool():
    """Test the calculator tool directly."""
    from tools.calculator import CalculatorTool
    calc = CalculatorTool()

    assert "22" in calc.run("2 + 2 * 10")   # 22 (not 40, PEMDAS)
    assert "4" in calc.run("2 + 2")
    assert "10.0" in calc.run("sqrt(100)") or "10" in calc.run("sqrt(100)")
    assert "Error" in calc.run("")            # Empty input
    assert "Error" in calc.run("__import__('os')")  # Unsafe input blocked
    print("✓ Calculator tool works correctly")


def test_datetime_tool():
    """Test the datetime tool directly."""
    from tools.datetime_tool import DateTimeTool
    dt = DateTimeTool()

    result = dt.run("current date and time")
    assert "Date" in result or "date" in result.lower()
    print(f"✓ DateTime tool works: {result[:50]}...")


def test_summarizer_tool():
    """Test the summarizer tool directly."""
    from tools.summarizer import TextSummarizerTool
    summarizer = TextSummarizerTool()

    long_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, 
    as opposed to the natural intelligence displayed by animals including humans. 
    AI research has been defined as the field of study of intelligent agents, 
    which refers to any system that perceives its environment and takes actions 
    that maximize its chance of achieving its goals. The term artificial intelligence 
    had previously been used to describe machines that mimic and display human 
    cognitive skills associated with the human mind, such as learning and problem-solving. 
    This definition has since been rejected by major AI researchers who now describe 
    AI in terms of rationality and acting rationally, which does not limit how 
    intelligence can be articulated.
    """

    result = summarizer.run(long_text, max_sentences=2)
    assert "Summary" in result
    assert len(result) < len(long_text)
    print("✓ Text summarizer works correctly")


def test_tool_registry():
    """Test that the tool registry finds and runs tools correctly."""
    from tools.tool_registry import tool_registry

    # Should find all 4 tools
    assert len(tool_registry.get_tool_names()) == 4

    # Should run a tool by name
    result = tool_registry.run_tool("Calculator", "10 + 5")
    assert "15" in result

    # Should handle unknown tool gracefully
    result = tool_registry.run_tool("UnknownTool", "test")
    assert "not found" in result.lower()

    print("✓ Tool registry works correctly")


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Running AI Research Assistant Agent Tests")
    print("=" * 50 + "\n")

    # Run tests that don't need an API key
    test_health_check()
    test_root_endpoint()
    test_tools_endpoint()
    test_history_empty()
    test_history_limit_parameter()
    test_agent_empty_query()
    test_agent_whitespace_query()
    test_agent_missing_query()
    test_agent_query_too_short()
    test_calculator_tool()
    test_datetime_tool()
    test_summarizer_tool()
    test_tool_registry()

    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)
