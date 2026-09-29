#!/usr/bin/env bash
# ==============================================================================
#  NotGoogle - Full Stack One-Click Stop Script
#  Gracefully stops backend, frontend, and Docker containers
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/NotGoogle"

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${YELLOW}Stopping all NotGoogle processes...${NC}"

# Kill processes on port 8000 (Backend) and port 5173 (Frontend)
for port in 8000 5173; do
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo -e "  Freeing port $port (PID: $pids)..."
    kill -9 $pids 2>/dev/null || true
  else
    echo -e "  Port $port is already free."
  fi
done

# Stop Docker container if running
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo -e "  Stopping SearXNG container..."
  (cd "$BACKEND_DIR" && docker compose stop searxng >/dev/null 2>&1 || true)
fi

echo -e "${GREEN}✔ All NotGoogle services stopped successfully.${NC}"
