#!/usr/bin/env bash
# ==============================================================================
# NexusAudit Lab Automated Reset Script
# Cleans exploitation artifacts and restores clean baseline state.
# Run as: root (sudo ./reset.sh)
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Error: reset.sh must be run as root.${NC}"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}[*] Resetting NexusAudit machine to pristine state...${NC}"

# 1. Terminate any reverse shell / background nc/socat/sh processes spawned by nexusaudit
echo -n "[*] Terminating attacker processes... "
pkill -u nexusaudit -f "nc|bash|sh|socat|python" 2>/dev/null || true
echo -e "${GREEN}Done${NC}"

# 2. Clean temporary directories of attacker artifacts
echo -n "[*] Purging temporary files in /tmp and /var/tmp... "
rm -rf /tmp/* /tmp/.* 2>/dev/null || true
rm -rf /var/tmp/* /var/tmp/.* 2>/dev/null || true
echo -e "${GREEN}Done${NC}"

# 3. Restore system binary permissions
echo -n "[*] Restoring system binary permissions (removing SUID bits)... "
chmod 755 /bin/bash /usr/bin/bash 2>/dev/null || true
echo -e "${GREEN}Done${NC}"

# 4. Restore challenge flags
echo -n "[*] Restoring challenge flags... "
echo "flag{n3xus_4ud1t_ssrf_2_jwt_f0rg3ry_rce_98124}" > /home/nexusaudit/user.txt
chown nexusaudit:nexus /home/nexusaudit/user.txt
chmod 640 /home/nexusaudit/user.txt

echo "flag{n3xus_c0r3_1pc_dl0p3n_p4th_tr4v3rs4l_r00t_99012}" > /root/root.txt
chown root:root /root/root.txt
chmod 600 /root/root.txt
echo -e "${GREEN}Done${NC}"

# 5. Restart services
echo -n "[*] Restarting Nexus services... "
systemctl restart nexus-internal.service
systemctl restart nexus-web.service
systemctl restart nexus-manager.service
systemctl restart nginx
sleep 2
echo -e "${GREEN}Done${NC}"

# 6. Run healthcheck to verify
echo -e "${BLUE}[*] Running post-reset health check:${NC}"
"${SCRIPT_DIR}/healthcheck.sh"
