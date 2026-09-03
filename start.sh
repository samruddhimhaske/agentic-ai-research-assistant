#!/bin/bash
# ============================================================
# start.sh — AI Research Assistant Agent ko start karo
# Double-click karo ya terminal mein: bash start.sh
# ============================================================

echo ""
echo "🤖 AI Research Assistant Agent Starting..."
echo "============================================"

# Project folder mein jao
cd "$(dirname "$0")"

# Virtual environment activate karo
source venv/bin/activate

# Frontend automatically browser mein kholo
echo "🌐 Opening frontend in browser..."
open frontend/index.html

echo ""
echo "✅ Server chal raha hai: http://localhost:8000"
echo "📖 API Docs:             http://localhost:8000/docs"
echo ""
echo "⛔ Band karne ke liye: Ctrl + C dabaao"
echo "============================================"
echo ""

# Backend server start karo
cd backend
uvicorn main:app --reload --port 8000
