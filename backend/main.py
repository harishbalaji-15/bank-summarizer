"""
FastAPI application entry point for the Bank Statement Summarizer backend.
Run with: python main.py  (or uvicorn main:app --reload)
"""
from __future__ import annotations

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers.parse import router as parse_router

app = FastAPI(
    title="Bank Statement Summarizer API",
    description="Offline-first API to parse and summarise bank statements (PDF/CSV/Excel).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parse_router)


@app.get("/health")
def health():
    return {"status": "ok", "message": "Bank Statement Summarizer is running"}


# Serve frontend build if present (for single-container deployments like Hugging Face Spaces)
dist_dirs = [
    os.path.join(os.path.dirname(__file__), "frontend_dist"),
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"),
]
frontend_dist = next((d for d in dist_dirs if os.path.exists(d)), None)

if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("health", "docs", "openapi.json"):
            raise HTTPException(status_code=404)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 7860))
    print(f"\n[OK] Backend running at http://0.0.0.0:{port}")
    print(f"     Access API docs at http://0.0.0.0:{port}/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
