"""
config.py - Application Configuration
======================================
This file loads all settings from environment variables (.env file).
Using a central config file means you only need to change settings in ONE place.

How it works:
- We use pydantic-settings to read values from the .env file automatically.
- If a variable is missing from .env, it falls back to a safe default value.
- The `config` object is imported by other files that need these settings.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load the .env file from the project root directory
# This makes all the variables in .env available to our app
load_dotenv()


class Settings(BaseSettings):
    """
    Settings class - All application configuration lives here.
    
    Each field reads from the matching environment variable.
    The 'default' value is used if the variable isn't set.
    """

    # --- OpenAI / LLM Settings ---
    openai_api_key: str = Field(
        default="your_api_key_here",
        description="Your OpenAI API key"
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        description="The AI model to use"
    )

    # --- Groq Free Alternative ---
    use_groq: bool = Field(default=False, description="Use Groq instead of OpenAI")
    groq_api_key: str = Field(default="", description="Groq API key (free)")
    groq_model: str = Field(default="llama-3.1-8b-instant", description="Groq model name")

    # --- Application Settings ---
    debug: bool = Field(
        default=True,
        description="Enable debug mode for detailed error messages"
    )
    app_host: str = Field(
        default="0.0.0.0",
        description="Host address to run the server on"
    )
    app_port: int = Field(
        default=8000,
        description="Port number for the server"
    )

    # --- CORS (Cross-Origin Resource Sharing) Settings ---
    # CORS allows your frontend (on a different URL) to talk to your backend
    allowed_origins: str = Field(
        default="*",
        description="Allowed frontend origins (use * for development)"
    )

    # --- Agent Behavior Settings ---
    max_iterations: int = Field(
        default=5,
        description="Maximum thinking loops before the agent stops"
    )
    max_history_size: int = Field(
        default=50,
        description="How many past queries to keep in history"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        # Fix: don't treat 'model_' as a reserved namespace
        "protected_namespaces": (),
    }


# Create a single global settings object
# Other files import this: from config import settings
settings = Settings()


def get_allowed_origins() -> list[str]:
    """
    Parse the ALLOWED_ORIGINS string into a list.
    
    Example: "http://localhost:3000,https://myapp.vercel.app"
    becomes: ["http://localhost:3000", "https://myapp.vercel.app"]
    """
    origins_str = settings.allowed_origins
    if origins_str == "*":
        return ["*"]
    # Split by comma and strip whitespace
    return [origin.strip() for origin in origins_str.split(",")]
