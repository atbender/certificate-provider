import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import uvicorn
from pydantic import BaseModel

from src.core.k8s_certificate import (
    validate_certificate,
    generate_certificate,
    save_certificate_data,
    generate_secure_certificate_id,
    generate_verification_code,
    CERT_DB_FILE
)

app = FastAPI(
    title="Certificate Management API",
    description="API for generating and validating Kubernetes certification credentials",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    raise ValueError("ADMIN_TOKEN environment variable must be set")

api_key_header = APIKeyHeader(name="X-Admin-Token")

def verify_admin_token(api_key: str = Depends(api_key_header)):
    if api_key != ADMIN_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin token"
        )
    return api_key

class ValidationRequest(BaseModel):
    certificate_id: str
    verification_code: str = None

class ValidationResponse(BaseModel):
    valid: bool
    certificate_data: dict = None
    message: str = None

class CertificateRequest(BaseModel):
    student_name: str
    course_name: str
    issue_date: str = None
    instructor: str = ""
    co_instructor: str = ""

class CertificateResponse(BaseModel):
    certificate_id: str
    verification_code: str
    pdf_path: str

@app.get("/")
async def root():
    return {
        "name": "Certificate Management API",
        "version": "1.0.0",
        "description": "API for generating and validating Kubernetes certificates"
    }

def validate_and_respond(certificate_id, verification_code):
    if not os.path.exists(CERT_DB_FILE):
        raise HTTPException(status_code=503, detail="Certificate database not available")

    is_valid, cert_data = validate_certificate(certificate_id, verification_code)

    if is_valid:
        return ValidationResponse(
            valid=True,
            certificate_data={
                "id": cert_data["id"],
                "student_name": cert_data["student_name"],
                "course_name": cert_data["course_name"],
                "issue_date": cert_data["issue_date"],
                "instructor": cert_data.get("instructor", ""),
                "co_instructor": cert_data.get("co_instructor", "")
            }
        )
    elif cert_data:
        return ValidationResponse(
            valid=False,
            message="Invalid verification code"
        )
    else:
        return ValidationResponse(
            valid=False,
            message="Certificate not found"
        )

@app.get("/validate")
async def validate_get(
    certificate_id: str = Query(..., description="Certificate ID to validate"),
    verification_code: str = Query(None, description="Optional verification code")
):
    return validate_and_respond(certificate_id, verification_code)

@app.post("/validate")
async def validate_post(request: ValidationRequest):
    return validate_and_respond(request.certificate_id, request.verification_code)

@app.post("/generate", response_model=CertificateResponse)
async def generate_certificate_endpoint(
    request: CertificateRequest,
    token: str = Depends(verify_admin_token)
):
    issue_date = request.issue_date or datetime.now().strftime("%Y-%m-%d")
    
    cert_id = generate_secure_certificate_id(
        request.student_name,
        request.course_name,
        issue_date
    )
    
    verification_code = generate_verification_code(
        cert_id,
        request.student_name,
        request.course_name
    )
    
    pdf_path = generate_certificate(
        request.student_name,
        request.course_name,
        request.instructor,
        request.co_instructor,
        issue_date,
        cert_id
    )
    
    save_certificate_data(
        cert_id,
        verification_code,
        request.student_name,
        request.course_name,
        issue_date,
        request.instructor,
        request.co_instructor
    )
    
    return CertificateResponse(
        certificate_id=cert_id,
        verification_code=verification_code,
        pdf_path=pdf_path
    )

def start_api_server(host="0.0.0.0", port=8000):
    uvicorn.run("src.api.api:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    start_api_server()
