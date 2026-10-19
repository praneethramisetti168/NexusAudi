from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class WebhookTestRequest(BaseModel):
    url: str = Field(..., description="Target callback URL to test webhook delivery against")
    timeout: Optional[int] = Field(default=5, ge=1, le=10, description="Connection timeout in seconds")

class FormulaEvaluateRequest(BaseModel):
    formula: str = Field(..., description="Mathematical aggregation formula")
    sample_data: Optional[Dict[str, Any]] = None

class WebhookTestResponse(BaseModel):
    status: str
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None

class FormulaEvaluateResponse(BaseModel):
    status: str
    formula: str
    result: Optional[Any] = None
    error: Optional[str] = None
