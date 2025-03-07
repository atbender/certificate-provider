from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.validation import app as validation_app
from src.api.web import app as web_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api", validation_app)

for route in web_app.routes:
    app.routes.append(route)

def start_api_server(host="0.0.0.0", port=8000):
    import uvicorn
    uvicorn.run("src.api.api:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    start_api_server()
