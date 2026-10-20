import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import company as company_api, live as live_api, telegram as telegram_api, adjustments, ai as ai_api, audit as audit_api, auth, payroll as payroll_api, documents, finance, reference, reports
from app.core import audit, events as live_events
from app.core.config import settings

if "dev-only" in settings.secret_key and not settings.database_url.startswith("sqlite"):
    raise RuntimeError("Set SECRET_KEY to a long random value before using a real database")

audit.install()
live_events.install()
log = logging.getLogger("daybook")
app = FastAPI(title="Prime Beton API", version="2.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=700, compresslevel=6)   # pages, scripts and JSON shrink 3-5x; the live event stream is never compressed

for r in (auth.router, reference.router, documents.router, adjustments.router, telegram_api.router, payroll_api.router, finance.router, reports.router, audit_api.router, ai_api.router, live_api.router, company_api.router):
    app.include_router(r, prefix="/api")


@app.middleware("http")
async def access_log(request: Request, call_next):
    rid, t0 = uuid.uuid4().hex[:8], time.perf_counter()
    resp = await call_next(request)
    resp.headers["X-Request-ID"] = rid
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(self), geolocation=()")
    if request.url.path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")            # business data is never kept by a browser or proxy cache
    else:
        resp.headers.setdefault("Cache-Control", "no-cache")            # the page files are re-checked on every load, so a new version shows at once
    if request.url.path.startswith("/api/") and request.url.path != "/api/health":
        log.info("%s %s %s %s %.0fms", rid, request.method, request.url.path, resp.status_code, (time.perf_counter() - t0) * 1000)
    return resp


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "error", "message": str(exc.detail), "params": {}}
    return JSONResponse({"detail": detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(x) for x in first.get("loc", []) if x != "body")
    return JSONResponse({"detail": {"code": "invalid", "message": f"{loc}: {first.get('msg', 'invalid value')}",
                                    "params": {"field": loc}}}, status_code=422)


@app.get("/api/health")
def health():
    return {"status": "ok", "demo_users": settings.seed_demo_users}


# The frontend is served by the same process, so one container is enough.
_front = Path(settings.frontend_dir)
if _front.is_dir():
    app.mount("/", StaticFiles(directory=_front, html=True), name="frontend")
