import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from src.core.certificate_renderer import (
    validate_certificate,
    generate_certificate,
    save_certificate_data,
    generate_secure_certificate_id,
    generate_verification_code,
    CERT_DB_FILE
)


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
    issue_date: str
    instructor: str
    instructor_title: str
    co_instructor: str
    co_instructor_title: str
    organization: str
    place: str
    certification_type: str
    hours: str


class CertificateResponse(BaseModel):
    certificate_id: str
    verification_code: str


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
                "instructor_title": cert_data.get("instructor_title", ""),
                "co_instructor": cert_data.get("co_instructor", ""),
                "co_instructor_title": cert_data.get("co_instructor_title", ""),
                "organization": cert_data.get("organization", ""),
                "place": cert_data.get("place", ""),
                "certification_type": cert_data.get("certification_type", ""),
                "hours": cert_data.get("hours", "")
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


def generate_certificate_pdf(cert_data):
    try:
        pdf_path = generate_certificate(
            cert_data["student_name"],
            cert_data["course_name"],
            cert_data["issue_date"],
            cert_data.get("instructor", ""),
            cert_data.get("instructor_title", ""),
            cert_data.get("co_instructor", ""),
            cert_data.get("co_instructor_title", ""),
            cert_data.get("organization", ""),
            cert_data.get("place", ""),
            cert_data.get("certification_type", ""),
            cert_data.get("hours", ""),
            cert_data["id"]
        )
        return pdf_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


api_app = FastAPI(
    title="Certificate Management API",
    description="API for generating and validating Kubernetes certification credentials",
    version="1.0.0"
)

api_app.add_middleware(
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


@api_app.get("/")
async def api_root():
    return {
        "name": "Certificate Management API",
        "version": "1.0.0",
        "description": "API for generating and validating Kubernetes certificates"
    }


@api_app.get("/validate")
async def validate_get(
    certificate_id: str = Query(..., description="Certificate ID to validate"),
    verification_code: str = Query(None, description="Optional verification code")
):
    return validate_and_respond(certificate_id, verification_code)


@api_app.post("/validate")
async def validate_post(request: ValidationRequest):
    return validate_and_respond(request.certificate_id, request.verification_code)


@api_app.post("/generate", response_model=CertificateResponse)
async def generate_certificate_endpoint(
    request: CertificateRequest,
    token: str = Depends(verify_admin_token)
):
    cert_id = generate_secure_certificate_id(
        request.student_name,
        request.course_name,
        request.issue_date
    )

    verification_code = generate_verification_code(
        cert_id,
        request.student_name,
        request.course_name
    )

    pdf_path = generate_certificate(
        request.student_name,
        request.course_name,
        request.issue_date,
        request.instructor,
        request.instructor_title,
        request.co_instructor,
        request.co_instructor_title,
        request.organization,
        request.place,
        request.certification_type,
        request.hours,
        cert_id
    )

    save_certificate_data(
        cert_id,
        verification_code,
        request.student_name,
        request.course_name,
        request.issue_date,
        request.instructor,
        request.instructor_title,
        request.co_instructor,
        request.co_instructor_title,
        request.organization,
        request.place,
        request.certification_type,
        request.hours
    )

    return CertificateResponse(
        certificate_id=cert_id,
        verification_code=verification_code
    )

web_app = FastAPI()

web_dir = Path(__file__).parent.parent / 'web'

web_app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@web_app.get("/", response_class=HTMLResponse)
async def get_validation_page():
    try:
        with open(web_dir / 'index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Validation page not found")


@web_app.get("/validate")
async def validate_certificate_web(certificate_id: str, verification_code: str, request: Request):
    validation_response = validate_and_respond(certificate_id, verification_code)

    accept_header = request.headers.get("accept", "")

    if "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest":
        if not validation_response.valid:
            return JSONResponse({
                "valid": False,
                "message": validation_response.message
            })

        return JSONResponse({
            "valid": True,
            "certificate_data": validation_response.certificate_data
        })

    return RedirectResponse(url=f"/?certificate_id={certificate_id}&verification_code={verification_code}")


@web_app.get("/view")
async def view_certificate(certificate_id: str, verification_code: str):
    validation_response = validate_and_respond(certificate_id, verification_code)

    if not validation_response.valid:
        raise HTTPException(status_code=404, detail="Invalid certificate")

    pdf_path = generate_certificate_pdf(validation_response.certificate_data)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf"
    )


@web_app.get("/download")
async def download_certificate(certificate_id: str, verification_code: str):
    validation_response = validate_and_respond(certificate_id, verification_code)

    if not validation_response.valid:
        raise HTTPException(status_code=404, detail="Invalid certificate")

    pdf_path = generate_certificate_pdf(validation_response.certificate_data)

    return FileResponse(
        path=pdf_path,
        filename=f"certificate_{certificate_id}.pdf",
        media_type="application/pdf"
    )


def create_combined_app():
    """Create a combined FastAPI application with both API and web routes"""
    combined_app = FastAPI()

    combined_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    combined_app.mount("/api", api_app)

    for route in web_app.routes:
        combined_app.routes.append(route)

    return combined_app


app = create_combined_app()
