import os
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

from src.core.k8s_certificate import validate_certificate, CERT_DB_FILE

app = FastAPI(
    title="Certificate Validation API",
    description="API for validating Kubernetes certification credentials",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValidationRequest(BaseModel):
    certificate_id: str
    verification_code: str = None


class ValidationResponse(BaseModel):
    valid: bool
    certificate_data: dict = None
    message: str = None


@app.get("/")
async def root():
    return {
        "name": "Certificate Validation API",
        "version": "1.0.0",
        "description": "API for validating Kubernetes certificates"
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
                "issue_date": cert_data["issue_date"]
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


def start_api_server(host="0.0.0.0", port=8000):
    uvicorn.run("src.api.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    start_api_server()
