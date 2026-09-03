"""
services/history_service.py - Agent History Management
=======================================================
This service manages storing and retrieving the history of agent runs.

For simplicity, we store history IN MEMORY (a Python list).
This means history resets when the server restarts.

In a production app, you'd replace this with a real database like:
  - SQLite (simple file-based DB, great for beginners)
  - PostgreSQL (production-grade relational DB)
  - MongoDB (document-based NoSQL DB)

The service pattern means: if you ever switch from memory to a database,
you only change THIS file — nothing else needs to change.
"""

import uuid
from datetime import datetime
from models.schemas import HistoryItem, AgentResponse
from config import settings


class HistoryService:
    """
    Manages the in-memory history of agent interactions.
    
    Think of this as a simple notebook that records every
    question the user has asked and what the agent answered.
    """

    def __init__(self):
        # A simple Python list stores all history items
        # Newest items are added to the front (index 0)
        self._history: list[HistoryItem] = []

    def add_entry(self, response: AgentResponse) -> HistoryItem:
        """
        Save a new agent response to history.
        
        Called automatically after every successful agent run.
        
        Args:
            response: The complete AgentResponse from the agent
            
        Returns:
            The HistoryItem that was saved
        """
        # Generate a unique ID for this history entry
        entry_id = str(uuid.uuid4())[:8]  # Short 8-character ID

        # Extract just the tool names (not full details) for the history card
        tool_names = [tool.tool_name for tool in response.tools_used]

        # Create a short preview of the answer (first 200 characters)
        # Strip Markdown formatting for a clean preview
        answer_text = response.final_answer
        # Remove common Markdown symbols for cleaner preview
        for symbol in ["#", "*", "_", "`", "\n"]:
            answer_text = answer_text.replace(symbol, " ")
        answer_preview = answer_text.strip()[:200] + "..." if len(answer_text) > 200 else answer_text.strip()

        # Build the history item
        item = HistoryItem(
            id=entry_id,
            query=response.query,
            answer_preview=answer_preview,
            tools_used=tool_names,
            timestamp=response.timestamp or datetime.now().isoformat(),
            processing_time=response.processing_time
        )

        # Add to the FRONT of the list so newest shows first
        self._history.insert(0, item)

        # If we've exceeded the max history size, remove the oldest entry
        if len(self._history) > settings.max_history_size:
            self._history.pop()  # Remove last (oldest) item

        return item

    def get_history(self, limit: int = 20) -> list[HistoryItem]:
        """
        Retrieve the most recent history entries.
        
        Args:
            limit: Maximum number of entries to return (default: 20)
            
        Returns:
            List of HistoryItem objects, newest first
        """
        return self._history[:limit]

    def get_total_count(self) -> int:
        """Return how many entries are in history."""
        return len(self._history)

    def clear_history(self) -> None:
        """Clear all history entries. Useful for testing."""
        self._history.clear()


# Create a single shared instance of the history service
# This is called a "singleton" — one object used by the whole app
# Other files import this: from services.history_service import history_service
history_service = HistoryService()
