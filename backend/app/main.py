"""FastAPI 入口：静态瓦片托管 + API。"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import hmac

from .api import indicators, point, meta, data, preview, zones, soiledge, scientific, research, auth
from .scientific.research_store import connect, initialize

app = FastAPI(title="壤脉天玑 Scientific Intelligence", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:18651", "http://localhost:18651", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(indicators.router)
app.include_router(point.router)
app.include_router(meta.router)
app.include_router(data.router)
app.include_router(preview.router)
app.include_router(zones.router)
app.include_router(soiledge.router)
app.include_router(scientific.router)
app.include_router(research.router)
app.include_router(auth.router)


@app.middleware("http")
async def protect_research(request, call_next):
    if not request.url.path.startswith("/api/research/"):
        return await call_next(request)
    initialize()
    with connect() as con:
        auth.init_auth(con)
        session = auth.session_for(request, con)
    if not session:
        return JSONResponse({"detail": "请先登录"}, status_code=401)
    if request.method not in ("GET", "HEAD", "OPTIONS") and not hmac.compare_digest(
            request.headers.get("X-CSRF-Token", ""), session["csrf_token"]):
        return JSONResponse({"detail": "请求校验失败"}, status_code=403)
    token = auth.CURRENT_USER.set(session["user_id"])
    try:
        return await call_next(request)
    finally:
        auth.CURRENT_USER.reset(token)

TILES_DIR = Path(__file__).absolute().parents[1] / "static" / "tiles"
if TILES_DIR.is_dir():
    app.mount("/tiles", StaticFiles(directory=TILES_DIR), name="tiles")

_dist_assets = Path(__file__).absolute().parents[2] / "frontend" / "dist" / "assets"
if _dist_assets.exists():
    app.mount("/assets", StaticFiles(directory=_dist_assets), name="assets")

_account_dir = Path(__file__).absolute().parents[2] / "frontend" / "dist" / "account"
if _account_dir.is_dir():
    app.mount("/account", StaticFiles(directory=_account_dir, html=True), name="account")

_account_design_dir = Path(__file__).absolute().parents[2] / "frontend" / "dist" / "account-design"
if _account_design_dir.is_dir():
    app.mount("/account-design", StaticFiles(directory=_account_design_dir), name="account-design")


@app.get("/")
def index():
    frontend_dist = Path(__file__).absolute().parents[2] / "frontend" / "dist" / "index.html"
    if frontend_dist.exists():
        return FileResponse(frontend_dist)
    return {"message": "土壤健康数据平台 API", "docs": "/docs"}


@app.get('/analysis')
def research_page():
    frontend_dist = Path(__file__).absolute().parents[2] / 'frontend' / 'dist' / 'index.html'
    return FileResponse(frontend_dist)


@app.get('/evidence')
def evidence_page():
    frontend_dist = Path(__file__).absolute().parents[2] / 'frontend' / 'dist' / 'index.html'
    return FileResponse(frontend_dist)
