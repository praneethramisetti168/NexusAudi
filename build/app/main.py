"""
NexusAudit Compliance & Telemetry Web Platform
Main FastAPI Application Entrypoint
"""

import os
import time
import urllib.parse
import requests
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import (
    WebhookTestRequest,
    WebhookTestResponse,
    FormulaEvaluateRequest,
    FormulaEvaluateResponse
)
from .evaluator import safe_evaluate_formula, SandboxSecurityError
from .auth import verify_auditor_token

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="NexusAudit Enterprise Portal",
    description="Internal Continuous Compliance, Audit Aggregation and Telemetry Platform",
    version="2.4.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount templates and static directory
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Sample corporate audit logs for realistic presentation
SAMPLE_AUDIT_LOGS = [
    {"id": "AUD-9021", "timestamp": "2026-10-16 09:14:02", "actor": "svc_kubernetes_ci", "action": "IAM_ROLE_ASSUME", "resource": "arn:aws:iam::prod:role/deploy", "status": "SUCCESS"},
    {"id": "AUD-9022", "timestamp": "2026-10-16 10:22:15", "actor": "j.doe@corp.local", "action": "SECRET_READ", "resource": "vault://prod/db/analytics", "status": "SUCCESS"},
    {"id": "AUD-9023", "timestamp": "2026-10-16 11:05:49", "actor": "unknown_external", "action": "LOGIN_ATTEMPT", "resource": "portal_admin", "status": "DENIED"},
    {"id": "AUD-9024", "timestamp": "2026-10-16 12:31:00", "actor": "svc_backup_agent", "action": "SNAPSHOT_CREATE", "resource": "vol-08fae19b8821", "status": "SUCCESS"},
    {"id": "AUD-9025", "timestamp": "2026-10-16 14:18:33", "actor": "r.smith@corp.local", "action": "SECURITY_GROUP_MODIFY", "resource": "sg-09b11029e01", "status": "FLAGGED"}
]

def is_safe_url(url: str):
    """
    Corporate egress URL filter.
    Blocks known loopback and RFC1918 private IPv4 subnets.
    """
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False, "Invalid URL structure"

    if parsed.scheme not in ["http", "https"]:
        return False, "Only HTTP and HTTPS protocols are permitted"

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname in URL"

    # Corporate blocklist
    BLOCKED_PATTERNS = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "10.",
        "192.168.",
        "172.16.",
        "172.17.",
        "172.18.",
        "172.19.",
        "172.20.",
        "172.21.",
        "172.22.",
        "172.23.",
        "172.24.",
        "172.25.",
        "172.26.",
        "172.27.",
        "172.28.",
        "172.29.",
        "172.30.",
        "172.31.",
        "169.254."
    ]

    for pattern in BLOCKED_PATTERNS:
        if pattern in hostname:
            return False, f"Destination '{hostname}' is blocked: matches internal policy rule '{pattern}'"

    return True, "OK"

@app.get("/", response_class=HTMLResponse)
async def index_view(request: Request):
    """Compliance dashboard frontend"""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "logs": SAMPLE_AUDIT_LOGS,
            "stats": {
                "compliance_score": 98.4,
                "monitored_nodes": 42,
                "open_findings": 3,
                "last_scan": "Today, 14:00 UTC"
            }
        }
    )

@app.get("/api/v1/health")
async def health_check():
    """Public platform health check"""
    return {
        "status": "healthy",
        "service": "NexusAudit-Public-Portal",
        "version": "2.4.0",
        "timestamp": time.time()
    }

@app.get("/api/v1/audit/logs")
async def get_audit_logs():
    """Retrieve recent compliance audit logs"""
    return {"status": "success", "count": len(SAMPLE_AUDIT_LOGS), "data": SAMPLE_AUDIT_LOGS}

@app.post("/api/v1/webhook/test", response_model=WebhookTestResponse)
async def test_webhook(req: WebhookTestRequest):
    """
    Test alert webhook reachability and inspect remote status.
    Intended for DevOps to verify SIEM and Slack/PagerDuty notification endpoints.
    """
    safe, reason = is_safe_url(req.url)
    if not safe:
        return WebhookTestResponse(
            status="error",
            error=reason
        )

    start_time = time.time()
    try:
        # Perform outbound request
        resp = requests.get(
            req.url,
            timeout=req.timeout,
            headers={"User-Agent": "NexusAudit-WebhookValidator/2.4"},
            allow_redirects=True
        )
        latency = round((time.time() - start_time) * 1000, 2)
        
        headers_dict = {k: v for k, v in resp.headers.items()}
        return WebhookTestResponse(
            status="success",
            status_code=resp.status_code,
            headers=headers_dict,
            body=resp.text[:4096],
            latency_ms=latency
        )
    except requests.exceptions.RequestException as e:
        return WebhookTestResponse(
            status="error",
            error=f"Connection failed: {str(e)}"
        )

@app.post("/api/v1/audit/export/custom-formula", response_model=FormulaEvaluateResponse)
async def evaluate_custom_formula(
    req: FormulaEvaluateRequest,
    user_payload: dict = Depends(verify_auditor_token)
):
    """
    Execute mathematical metric calculations across audit telemetry.
    Protected: Requires valid Auditor cryptographic bearer token.
    """
    formula = req.formula.strip()
    if not formula:
        raise HTTPException(status_code=400, detail="Formula cannot be empty")

    try:
        result = safe_evaluate_formula(formula, req.sample_data)
        return FormulaEvaluateResponse(
            status="success",
            formula=formula,
            result=result
        )
    except SandboxSecurityError as se:
        return FormulaEvaluateResponse(
            status="sandbox_violation",
            formula=formula,
            error=str(se)
        )
    except Exception as e:
        return FormulaEvaluateResponse(
            status="execution_error",
            formula=formula,
            error=f"Evaluation failed: {str(e)}"
        )
