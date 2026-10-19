#!/usr/bin/env bash
# ==============================================================================
# NexusAudit Lab Automated Deployment Script
# Target Platform: Ubuntu 24.04 LTS (x86_64)
# Run as: root (sudo ./setup.sh)
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}[*] =====================================================${NC}"
echo -e "${BLUE}[*]       Deploying NexusAudit Security Challenge Lab      ${NC}"
echo -e "${BLUE}[*] =====================================================${NC}"

# 1. Verify root execution
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Error: setup.sh must be executed with root privileges.${NC}"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 2. Update packages and install dependencies
echo -e "${BLUE}[*] Step 1/8: Installing system packages & build tools...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y || true
apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-pip \
    nginx \
    gcc \
    make \
    curl \
    net-tools \
    socat \
    netcat-openbsd

# 3. Create service accounts and groups
echo -e "${BLUE}[*] Step 2/8: Configuring service accounts and groups...${NC}"
if ! getent group nexus >/dev/null; then
    groupadd -r nexus
    echo -e "${GREEN}[+] Created group: nexus${NC}"
fi

if ! id -u nexusaudit >/dev/null 2>&1; then
    useradd -r -g nexus -m -d /home/nexusaudit -s /bin/bash nexusaudit
    echo -e "${GREEN}[+] Created user: nexusaudit (UID: $(id -u nexusaudit), GID: $(id -g nexusaudit))${NC}"
else
    usermod -a -G nexus nexusaudit
fi

# 4. Create directory structure
echo -e "${BLUE}[*] Step 3/8: Initializing directory tree under /opt/nexus...${NC}"
mkdir -p /opt/nexus/app
mkdir -p /opt/nexus/internal_svc
mkdir -p /opt/nexus/daemon
mkdir -p /opt/nexus/bin
mkdir -p /usr/lib/nexus/modules
mkdir -p /var/log/nexus
mkdir -p /run/nexus

# 5. Deploy application files
echo -e "${BLUE}[*] Step 4/8: Deploying application source files...${NC}"
cp -r "${SCRIPT_DIR}/app"/* /opt/nexus/app/
cp -r "${SCRIPT_DIR}/internal_svc"/* /opt/nexus/internal_svc/
cp -r "${SCRIPT_DIR}/daemon"/* /opt/nexus/daemon/

# Deploy nexus-cli tool
cp "${SCRIPT_DIR}/daemon/nexus-cli.py" /usr/local/bin/nexus-cli
chmod 755 /usr/local/bin/nexus-cli

# 6. Build daemon and modules
echo -e "${BLUE}[*] Step 5/8: Compiling daemon and shared libraries...${NC}"
cd /opt/nexus/daemon
make clean || true
make all
cp sys_stat.so /usr/lib/nexus/modules/
chmod 755 /opt/nexus/daemon/nexus-manager
chmod 755 /usr/lib/nexus/modules/sys_stat.so

# 7. Setup Python Virtual Environment
echo -e "${BLUE}[*] Step 6/8: Setting up Python virtual environment...${NC}"
python3 -m venv /opt/nexus/venv
/opt/nexus/venv/bin/pip install --upgrade pip
/opt/nexus/venv/bin/pip install -r /opt/nexus/app/requirements.txt

# Fix permissions
chown -R root:nexus /opt/nexus
chmod -R 750 /opt/nexus
chmod -R 755 /opt/nexus/venv
chown -R nexusaudit:nexus /var/log/nexus
chmod 775 /var/log/nexus
chown -R root:nexus /run/nexus
chmod 775 /run/nexus

# 8. Setup Flags
echo -e "${BLUE}[*] Step 7/8: Seeding challenge flags...${NC}"
echo "flag{n3xus_4ud1t_ssrf_2_jwt_f0rg3ry_rce_98124}" > /home/nexusaudit/user.txt
chown nexusaudit:nexus /home/nexusaudit/user.txt
chmod 640 /home/nexusaudit/user.txt

echo "flag{n3xus_c0r3_1pc_dl0p3n_p4th_tr4v3rs4l_r00t_99012}" > /root/root.txt
chown root:root /root/root.txt
chmod 600 /root/root.txt

# 9. Configure Services and Nginx
echo -e "${BLUE}[*] Step 8/8: Enabling systemd services and Nginx reverse proxy...${NC}"
cp "${SCRIPT_DIR}/systemd/nexus-internal.service" /etc/systemd/system/
cp "${SCRIPT_DIR}/systemd/nexus-web.service" /etc/systemd/system/
cp "${SCRIPT_DIR}/systemd/nexus-manager.service" /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now nexus-internal.service
systemctl enable --now nexus-web.service
systemctl enable --now nexus-manager.service

# Configure Nginx
rm -f /etc/nginx/sites-enabled/default
cp "${SCRIPT_DIR}/nginx/nexusaudit.conf" /etc/nginx/sites-available/nexusaudit.conf
ln -sf /etc/nginx/sites-available/nexusaudit.conf /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Give services 2 seconds to initialize
sleep 2

echo -e "${GREEN}[+] =====================================================${NC}"
echo -e "${GREEN}[+]      NexusAudit Deployment Completed Successfully!   ${NC}"
echo -e "${GREEN}[+] =====================================================${NC}"
echo -e "Web Interface:      http://<TARGET_IP>:80/"
echo -e "API Documentation:  http://<TARGET_IP>:80/docs"
echo -e "Internal Microsvc:  http://127.0.0.1:8081/internal/health"
echo -e "IPC Unix Socket:    /run/nexus/manager.sock"
echo -e "Run '${SCRIPT_DIR}/healthcheck.sh' to verify all components."
