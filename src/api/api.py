from src.api.certificate_service import app

import uvicorn


def start_api_server(host="0.0.0.0", port=8000):
    uvicorn.run("src.api.api:app", host=host, port=port, reload=False)
