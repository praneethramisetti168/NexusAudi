"""
NexusAudit Authentication & JWT Verification Module
Verifies auditor/admin cryptographic signatures.
"""

import jwt
from fastapi import Header, HTTPException, status
from typing import Optional

# Internal cluster secret configured across services
JWT_SECRET = "n3xUs_4ud1t_hM4c_s3cr3t_k3y_982341"
JWT_ALGORITHM = "HS256"
ALLOWED_ROLES = ["auditor", "admin", "compliance_lead"]

def verify_auditor_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validates Bearer token from request header.
    Requires role 'auditor', 'admin', or 'compliance_lead'.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing. Required format: 'Bearer <token>'"
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'"
        )

    token = parts[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Cryptographic verification failed: {str(e)}"
        )

    role = payload.get("role")
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient role '{role}'. Allowed roles: {ALLOWED_ROLES}"
        )

    return payload
