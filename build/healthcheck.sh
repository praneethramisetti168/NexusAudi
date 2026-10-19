#!/usr/bin/env bash
# ==============================================================================
# NexusAudit Lab Health Check Script
# Verifies all services, ports, and internal endpoints are operational.
# ==============================================================================

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

echo -e "${BLUE}[*] =====================================================${NC}"
echo -e "${BLUE}[*]          NexusAudit Environment Health Check         ${NC}"
echo -e "${BLUE}[*] =====================================================${NC}"

# Check 1: Nginx service and port 80
echo -n "[*] Checking Port 80 (Nginx Reverse Proxy)... "
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ | grep -qE "200|301|302"; then
    echo -e "${GREEN}[PASS] (HTTP 200 OK)${NC}"
else
    echo -e "${RED}[FAIL] (Nginx not responding on port 80)${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: nexus-web service and port 8000
echo -n "[*] Checking Port 8000 (FastAPI Core Backend)... "
if curl -s http://127.0.0.1:8000/api/v1/health | grep -q "NexusAudit-Public-Portal"; then
    echo -e "${GREEN}[PASS] (Backend API Operational)${NC}"
else
    echo -e "${RED}[FAIL] (Backend not responding on port 8000)${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: nexus-internal service and port 8081
echo -n "[*] Checking Port 8081 (Internal Key Manager Microservice)... "
if curl -s http://127.0.0.1:8081/internal/health | grep -q "nexus-core-01"; then
    echo -e "${GREEN}[PASS] (Internal Microservice Operational)${NC}"
else
    echo -e "${RED}[FAIL] (Internal microservice not responding on 8081)${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: Unix Socket /run/nexus/manager.sock
echo -n "[*] Checking IPC Socket (/run/nexus/manager.sock)... "
if [ -S /run/nexus/manager.sock ]; then
    CLI_OUT=$(nexus-cli ping 2>/dev/null || true)
    if echo "$CLI_OUT" | grep -q "pong"; then
        echo -e "${GREEN}[PASS] (Daemon responsive to IPC ping)${NC}"
    else
        echo -e "${RED}[FAIL] (Socket exists but daemon didn't reply 'pong')${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}[FAIL] (Socket file /run/nexus/manager.sock missing)${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: User and Root Flag verification
echo -n "[*] Checking Challenge Flags... "
if [ -f /home/nexusaudit/user.txt ] && [ -f /root/root.txt ]; then
    echo -e "${GREEN}[PASS] (user.txt and root.txt present)${NC}"
else
    echo -e "${RED}[FAIL] (Flag files missing)${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo -e "${BLUE}[*] =====================================================${NC}"
if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}[+] ALL CHECKS PASSED. The NexusAudit lab is 100% operational!${NC}"
    exit 0
else
    echo -e "${RED}[!] HEALTH CHECK FAILED: $ERRORS test(s) failed. Check systemctl logs.${NC}"
    exit 1
fi
