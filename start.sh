#!/usr/bin/env bash
# ==============================================================================
#  NotGoogle - Full Stack One-Click Startup Script
#  Launches: Docker (SearXNG) + FastAPI Backend + React Vite Frontend
# ==============================================================================

set -e

# Resolve directory paths
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/NotGoogle"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Colors for terminal styling
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================================${NC}"
echo -e "${BOLD}${BLUE}N${RED}o${YELLOW}t${BLUE}G${GREEN}o${RED}o${BLUE}g${GREEN}l${RED}e${NC} - Full Stack Startup"
echo -e "${CYAN}Privacy-Preserving Search Engine & Continuous Crawler${NC}"
echo -e "${BLUE}=================================================================${NC}\n"

# Helper to check if a port is in use and free it
free_port() {
  local port=$1
  local pids
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo -e "${YELLOW}⚠️  Port $port is currently in use (PID: $pids). Freeing it...${NC}"
    kill -9 $pids 2>/dev/null || true
    sleep 1
  fi
}

free_port 8000
free_port 5173

# ------------------------------------------------------------------------------
# 1. Start Docker Services (SearXNG)
# ------------------------------------------------------------------------------
echo -e "${BOLD}[1/3] Checking Docker Services...${NC}"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo -e "  ${GREEN}✔ Docker daemon is running.${NC}"
    echo -e "  Starting SearXNG metasearch service..."
    (cd "$BACKEND_DIR" && docker compose up -d searxng)
    echo -e "  ${GREEN}✔ SearXNG running at http://localhost:8080${NC}"
  else
    echo -e "  ${YELLOW}⚠️  Docker daemon is not running. Starting without local SearXNG.${NC}"
    echo -e "     (Backend will operate seamlessly with local search & cloud storage)${NC}"
  fi
else
  echo -e "  ${YELLOW}⚠️  Docker command not found. Skipping SearXNG container.${NC}"
fi
echo ""

# ------------------------------------------------------------------------------
# 2. Start Backend (FastAPI + Hybrid Retriever + Crawler)
# ------------------------------------------------------------------------------
echo -e "${BOLD}[2/3] Starting Backend Server (FastAPI on Port 8000)...${NC}"
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo -e "  ${YELLOW}Virtual environment not found. Creating in $BACKEND_DIR/.venv...${NC}"
  python3 -m venv "$BACKEND_DIR/.venv"
  "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

# Launch backend in background
(
  cd "$BACKEND_DIR"
  source .venv/bin/activate
  exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
) &
BACKEND_PID=$!

echo -e "  Backend launched with PID: ${CYAN}$BACKEND_PID${NC}"
echo -e "  Waiting for backend to become healthy..."

# Healthcheck loop (up to 30s)
for i in {1..30}; do
  if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "  ${GREEN}✔ Backend is healthy and ready! (http://localhost:8000)${NC}"
    break
  fi
  sleep 1
  if [ $i -eq 30 ]; then
    echo -e "  ${RED}✖ Backend health check timed out. Please inspect backend logs.${NC}"
  fi
done
echo ""

# ------------------------------------------------------------------------------
# 3. Start Frontend (React 19 + Vite on Port 5173)
# ------------------------------------------------------------------------------
echo -e "${BOLD}[3/3] Starting Frontend Dev Server (Port 5173)...${NC}"
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo -e "  ${YELLOW}node_modules not found. Running npm install...${NC}"
  (cd "$FRONTEND_DIR" && npm install)
fi

# Launch frontend in background
(
  cd "$FRONTEND_DIR"
  exec npm run dev
) &
FRONTEND_PID=$!

echo -e "  Frontend launched with PID: ${CYAN}$FRONTEND_PID${NC}"
echo ""

# ------------------------------------------------------------------------------
# Cleanup handler on exit or Ctrl+C
# ------------------------------------------------------------------------------
cleanup() {
  echo -e "\n\n${YELLOW}Shutting down NotGoogle stack...${NC}"
  if [ -n "$BACKEND_PID" ]; then
    echo "  Stopping backend (PID: $BACKEND_PID)..."
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ]; then
    echo "  Stopping frontend (PID: $FRONTEND_PID)..."
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  
  # Also clean up any child processes on those ports
  free_port 8000
  free_port 5173
  
  echo -e "${GREEN}✔ All services safely stopped. Bye!${NC}"
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ------------------------------------------------------------------------------
# Ready Banner & Wait
# ------------------------------------------------------------------------------
echo -e "${GREEN}=================================================================${NC}"
echo -e "${BOLD}🚀 NotGoogle is fully operational!${NC}"
echo -e "   • ${BOLD}Frontend UI:${NC}       ${CYAN}http://localhost:5173${NC}"
echo -e "   • ${BOLD}Backend API Docs:${NC}  ${CYAN}http://localhost:8000/docs${NC}"
echo -e "   • ${BOLD}Crawler Status:${NC}    ${CYAN}http://localhost:8000/crawler/status${NC}"
if docker info >/dev/null 2>&1; then
  echo -e "   • ${BOLD}SearXNG Web:${NC}       ${CYAN}http://localhost:8080${NC}"
fi
echo -e "${GREEN}=================================================================${NC}"
echo -e "Press ${BOLD}Ctrl+C${NC} anytime to stop all services.\n"

# Keep the script running and stream logs until interrupted
wait
