from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.api.endpoints import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://deft-lollipop-d027aa.netlify.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates directory
templates = Jinja2Templates(directory="app/templates")

app.include_router(api_router)

@app.get("/")
async def root(request: Request):
    # Serve the HTML template
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok", "message": "API is running!"}
