# ============================================================
# Procfile — Process Configuration for Render / Heroku
# ============================================================
# A Procfile tells deployment platforms how to start your app.
# Render and Heroku both read this file automatically.
#
# Format: <process_type>: <command>
# "web" is the main web process that handles HTTP traffic.
#
# The $PORT variable is automatically set by the platform.
# ============================================================

web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
