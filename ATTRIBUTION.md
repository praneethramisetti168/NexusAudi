# Attribution & Originality Declaration

**Challenge Name:** NexusAudit  
**Author:** Praneeth Ramisetti  
**Submission Date:** October 2026  

---

## 1. Originality Declaration

I declare that **NexusAudit** is an original security challenge designed and developed specifically for this hiring technical assessment. 

* **No Direct Copying:** The challenge machine, attack path, source code, and scenarios have **not** been copied, cloned, or ported from Hack The Box, TryHackMe, VulnHub, PortSwigger Web Security Academy, CTFd repositories, or any other third-party platform.
* **Original Architecture:** The scenario, internal API interaction, custom AST evaluation sandbox, and the Unix Domain Socket IPC daemon with `dlopen()` path traversal vulnerability were architected and implemented from scratch.
* **Realistic Grounding:** The design reflects real-world engineering patterns found in modern cloud-native telemetry architectures:
  - An internal key-management microservice strictly bound to loopback.
  - Naive SSRF regex filtering vulnerable to IPv4 representation discrepancies.
  - Custom AST formula execution sandbox with attribute navigation vulnerabilities.
  - Privileged system daemons accepting IPC commands from group members with insufficient canonical path validation.

---

## 2. Components Created by the Author

| Component | File Path | Description |
| :--- | :--- | :--- |
| **AST Formula Evaluator** | `build/app/evaluator.py` | Custom Python AST visitor, node validator, and execution sandbox. |
| **Public Telemetry Web App** | `build/app/main.py`, `models.py`, `auth.py` | FastAPI application, URL validator, webhook testing engine, JWT authentication. |
| **Web UI Dashboard** | `build/app/templates/index.html`, `static/style.css` | Compliance dashboard frontend and diagnostic interface. |
| **Internal Telemetry Microservice** | `build/internal_svc/internal_api.py` | HTTP microservice providing cluster status and cryptographic metadata. |
| **Privileged IPC Daemon** | `build/daemon/nexus-manager.c` | Root Unix Domain Socket daemon handling IPC requests, module loading, and log rotation. |
| **IPC Management CLI** | `build/daemon/nexus-cli.py` | Command-line client for DevOps interaction with `nexus-manager.sock`. |
| **Diagnostic Shared Module** | `build/daemon/sys_stat.c` | Dynamic diagnostic shared library loaded via `dlopen()`. |
| **Automated Deployment & Testing** | `build/setup.sh`, `healthcheck.sh`, `reset.sh` | Idempotent bash automation for installation, health verification, and reset. |
| **Exploitation Suite** | `exploit/*.py`, `exploit/*.sh` | Exploit modules and full-chain automation PoC. |

---

## 3. Third-Party Libraries & Open Source References

The target machine incorporates standard open-source libraries and system utilities under permissive licenses:

| Software / Library | Version / Source | License | Usage |
| :--- | :--- | :--- | :--- |
| **Ubuntu Linux** | 24.04 LTS | Canonical / GPL | Target Host Operating System |
| **Nginx** | 1.24+ | BSD-2-Clause | Reverse Proxy on Port 80 |
| **Python** | 3.12+ | Python Software Foundation | Application Runtime |
| **FastAPI** | 0.110+ | MIT License | Web Framework |
| **Uvicorn** | 0.28+ | BSD-3-Clause | ASGI Web Server |
| **PyJWT** | 2.8+ | MIT License | JSON Web Token (JWT) Handling |
| **Requests** | 2.31+ | Apache 2.0 | HTTP Client for Webhook Testing |
| **Jinja2** | 3.1+ | BSD-3-Clause | Template Engine |
| **GCC & Make** | Standard distro | GPL | Compiler toolchain for C daemon |

---

## 4. Technical References

1. **SSRF & URL Parsing Discrepancies:**
   - RFC 3986: Uniform Resource Identifier (URI): Generic Syntax.
   - Orange Tsai, "A New Era of SSRF - Exploiting URL Parser in Trending Programming Languages", Black Hat USA 2017.
2. **Python Sandbox Escapes & AST Traversal:**
   - Python Official Documentation: `ast` — Abstract Syntax Trees (`ast.NodeVisitor`).
   - Ned Batchelder, "Eval really is dangerous" & Python class hierarchy introspection (`__subclasses__`).
3. **Privileged IPC & Dynamic Linker Vulnerabilities:**
   - Linux Programmer's Manual: `dlopen(3)`, `dlsym(3)`, `unix(7)`.
   - OWASP Top 10: API Security & Insecure Direct Object References in Local IPC.
