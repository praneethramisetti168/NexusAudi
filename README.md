# NexusAudit — Security Challenge Lab

**Candidate Name:** Praneeth Ramisetti  
**Machine Name:** NexusAudit  
**Package:** `PraneethRamisetti_NexusAudit.zip`  
**Domain:** Web Exploitation (Ubuntu 24.04 LTS)  
**Difficulty:** Medium – Hard  
**Evaluator Starting Access:** Remote Network Access (HTTP Port 80, no initial credentials)  
**Final Objective:** Root Access (`/root/root.txt`) and User Flag (`/home/nexusaudit/user.txt`)  

---

## 1. Scenario Description

**NexusAudit** is an enterprise continuous compliance and telemetry aggregation platform used by DevOps and Security Operations teams to monitor cloud workloads, verify notification webhooks, and calculate real-time compliance scores.

The platform architecture features:
* **Public Gateway:** Nginx reverse proxy on port 80 routing traffic to a Python FastAPI backend on port 8000.
* **Internal Microservice:** A key-management and telemetry microservice strictly bound to `127.0.0.1:8081` (unexposed to the internet).
* **Local Privileged Daemon:** A root-level IPC daemon (`nexus-manager`) listening on Unix Domain Socket `/run/nexus/manager.sock`, managing system diagnostics and log rotation for the `nexus` group.

---

## 2. Target Machine Hardware Requirements

* **Operating System:** Ubuntu 24.04 LTS (x86_64)
* **vCPU:** 4 – 8 vCPUs (Tested on 4 vCPUs)
* **RAM:** 8 GB – 16 GB (Operates stably on 4 GB+)
* **Storage:** 20 GB – 100 GB (Clean installation footprint < 6 GB)
* **Network:** Single virtual NIC (Bridged or Host-Only)
* **Dependencies:** Fully self-contained; no external cloud or SaaS services required at runtime.

---

## 3. Automated Deployment Instructions

The target is deployed starting from a clean installation of **Ubuntu 24.04 LTS**:

1. Transfer the challenge archive / `build/` files to the target machine (e.g. via SCP or shared folder):
   ```bash
   scp -r build/ user@<TARGET_IP>:/tmp/nexus_build
   ```
2. Log into the target machine via SSH or console:
   ```bash
   ssh user@<TARGET_IP>
   ```
3. Navigate to the build directory and execute `setup.sh` as `root`:
   ```bash
   cd /tmp/nexus_build
   sudo chmod +x setup.sh healthcheck.sh reset.sh
   sudo ./setup.sh
   ```
4. `setup.sh` will automatically:
   * Install necessary runtime packages (`nginx`, `python3-venv`, `gcc`, `make`, etc.).
   * Create service group `nexus` and service user `nexusaudit`.
   * Deploy the web portal, internal key microservice, and the root IPC daemon.
   * Compile the C daemon and diagnostic modules.
   * Configure Nginx reverse proxy on port 80.
   * Seed the challenge flags (`/home/nexusaudit/user.txt` and `/root/root.txt`).
   * Enable and launch the systemd services (`nexus-internal.service`, `nexus-web.service`, `nexus-manager.service`).

---

## 4. Health Checks

To verify that all services, ports, sockets, and flags are operational:

```bash
sudo /opt/nexus/healthcheck.sh
# or from build directory:
sudo ./healthcheck.sh
```

A healthy system outputs:
```
[*] Checking Port 80 (Nginx Reverse Proxy)... [PASS] (HTTP 200 OK)
[*] Checking Port 8000 (FastAPI Core Backend)... [PASS] (Backend API Operational)
[*] Checking Port 8081 (Internal Key Manager Microservice)... [PASS] (Internal Microservice Operational)
[*] Checking IPC Socket (/run/nexus/manager.sock)... [PASS] (Daemon responsive to IPC ping)
[*] Checking Challenge Flags... [PASS] (user.txt and root.txt present)
[+] ALL CHECKS PASSED. The NexusAudit lab is 100% operational!
```

---

## 5. Reset Instructions

To quickly restore the challenge machine back to its pristine baseline without reinstalling the operating system:

```bash
sudo /opt/nexus/reset.sh
# or from build directory:
sudo ./reset.sh
```

`reset.sh` performs:
* Termination of any lingering shell processes spawned by `nexusaudit`.
* Complete purging of `/tmp` and `/var/tmp` directories.
* Restoration of `/bin/bash` permissions (clearing any SUID bits).
* Restoration of challenge flags and permissions.
* Clean restart of all systemd services and Nginx.
* Execution of `healthcheck.sh` to confirm operational readiness.

---

## 6. Challenge Milestones & Flag Values

| Milestone | Attack Stage | Proof of Success |
| :--- | :--- | :--- |
| **Milestone 1** | SSRF & Filter Bypass | Extraction of internal HMAC signing key `n3xUs_4ud1t_hM4c_s3cr3t_k3y_982341` from `127.0.0.1:8081`. |
| **Milestone 2** | JWT Forgery & AST RCE | Remote shell as `nexusaudit` (UID 1001) and reading `/home/nexusaudit/user.txt`: <br>`flag{n3xus_4ud1t_ssrf_2_jwt_f0rg3ry_rce_98124}` |
| **Milestone 3** | Local PrivEsc via IPC `dlopen()` Path Traversal | Root access (`root` UID 0) and reading `/root/root.txt`: <br>`flag{n3xus_c0r3_1pc_dl0p3n_p4th_tr4v3rs4l_r00t_99012}` |

---

## 7. Package Contents

```
PraneethRamisetti_NexusAudit/
├── README.md                      # Overview, deployment, healthcheck, reset
├── ATTRIBUTION.md                 # References, originality declaration
├── build/                         # Target deployment scripts and source code
│   ├── app/                       # FastAPI web application, AST sandbox, UI templates
│   ├── internal_svc/              # Loopback key-management microservice (8081)
│   ├── daemon/                    # Root IPC daemon (nexus-manager) and nexus-cli
│   ├── nginx/                     # Reverse proxy configuration
│   ├── systemd/                   # Systemd service unit files
│   ├── setup.sh                   # One-click Ubuntu 24.04 automated installer
│   ├── healthcheck.sh             # Operational diagnostic script
│   └── reset.sh                   # Repeatable environment reset script
├── exploit/                       # Exploit scripts
│   ├── stage1_ssrf_leak.py        # SSRF key exfiltration script
│   ├── stage2_jwt_rce.py          # JWT generation & AST RCE exploit
│   ├── stage3_privesc.sh          # Local privilege escalation exploit
│   ├── full_chain_autopwn.py      # Master full-chain automation PoC
│   └── listener.py                # Standalone cross-platform reverse shell listener
├── writeup/
│   ├── WRITEUP.md                 # Detailed offensive walkthrough & technical explanations
│   └── screenshots/               # PoC screenshots (referenced in writeup)
└── video/
    └── walkthrough.mp4            # Complete video proof of concept walkthrough
```
