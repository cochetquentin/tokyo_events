"""Application FastAPI pour la carte des événements Tokyo."""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Tokyo Events Map",
    description="Carte interactive des événements à Tokyo",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Static files et templates
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

# Routes
from web.api import events, map as map_router
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(map_router.router, prefix="/api/map", tags=["map"])


@app.get("/")
async def root(request: Request):
    """Page d'accueil avec carte."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}
