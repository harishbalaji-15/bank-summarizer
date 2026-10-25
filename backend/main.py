"""
FastAPI application entry point for the Bank Statement Summarizer backend.
Run with: python main.py  (or uvicorn main:app --reload)
"""
from __future__ import annotations

import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.parse import router as parse_router

app = FastAPI(
    title="Bank Statement Summarizer API",
    description="Offline-first API to parse and summarise bank statements (PDF/CSV/Excel).",
    version="1.0.0",
)

# Allow Flutter web (localhost:any port) and mobile to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Offline app – safe to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parse_router)


@app.get("/health")
def health():
    return {"status": "ok", "message": "Bank Statement Summarizer is running"}


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"\n[OK] Backend running at http://localhost:{port}")
    print("     Access API docs at http://localhost:8000/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
