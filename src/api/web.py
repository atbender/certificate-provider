import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.core.k8s_certificate import validate_certificate, generate_certificate

app = FastAPI()

web_dir = Path(__file__).parent.parent / 'web'

app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_validation_page():
    try:
        with open(web_dir / 'index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Validation page not found")

@app.get("/validate")
async def validate_certificate_web(certificate_id: str, verification_code: str, request: Request):
    is_valid, cert_data = validate_certificate(certificate_id, verification_code)

    accept_header = request.headers.get("accept", "")

    if "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest":
        if not is_valid:
            return JSONResponse({"valid": False, "message": "Certificate not found"})

        return JSONResponse({
            "valid": True,
            "certificate_data": cert_data
        })

    return RedirectResponse(url=f"/?certificate_id={certificate_id}&verification_code={verification_code}")

@app.get("/view")
async def view_certificate(certificate_id: str, verification_code: str):
    is_valid, cert_data = validate_certificate(certificate_id, verification_code)

    if not is_valid:
        raise HTTPException(status_code=404, detail="Invalid certificate")

    try:
        pdf_path = generate_certificate(
            cert_data["student_name"],
            cert_data["course_name"],
            cert_data.get("instructor", ""),
            cert_data.get("co_instructor", ""),
            cert_data["issue_date"],
            cert_data["id"]
        )

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_certificate(certificate_id: str, verification_code: str):
    is_valid, cert_data = validate_certificate(certificate_id, verification_code)

    if not is_valid:
        raise HTTPException(status_code=404, detail="Invalid certificate")

    try:
        pdf_path = generate_certificate(
            cert_data["student_name"],
            cert_data["course_name"],
            cert_data.get("instructor", ""),
            cert_data.get("co_instructor", ""),
            cert_data["issue_date"],
            cert_data["id"]
        )

        return FileResponse(
            path=pdf_path,
            filename=f"certificate_{certificate_id}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
