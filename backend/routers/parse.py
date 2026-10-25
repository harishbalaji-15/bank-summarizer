"""
/api/parse  — upload endpoint.
Accepts PDF, CSV, XLSX, XLS and returns parsed statement data.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from parsers.pdf_parser import parse_pdf, PasswordRequiredError, InvalidPasswordError
from parsers.csv_excel_parser import parse_csv, parse_excel

router = APIRouter(prefix="/api", tags=["parse"])

_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/parse")
async def parse_statement(
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
):
    content = await file.read()

    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    filename = (file.filename or "").lower()
    ext = os.path.splitext(filename)[1]

    try:
        if ext == ".pdf":
            result = parse_pdf(content, password=password)
        elif ext == ".csv":
            result = parse_csv(content)
        elif ext in (".xlsx", ".xls"):
            result = parse_excel(content)
        else:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type '{ext}'. Upload PDF, CSV, XLSX or XLS.",
            )
    except PasswordRequiredError as exc:
        return JSONResponse(
            status_code=401,
            content={
                "error": "PASSWORD_REQUIRED",
                "detail": str(exc) or "This statement is password-protected. Please enter the password to unlock it.",
            },
        )
    except InvalidPasswordError as exc:
        return JSONResponse(
            status_code=401,
            content={
                "error": "INVALID_PASSWORD",
                "detail": str(exc) or "Incorrect password. For bank statements, this is often your Date of Birth (DDMMYYYY) or registered mobile number.",
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {exc}") from exc

    return JSONResponse(content=_enrich(result))


def _enrich(result: dict) -> dict:
    """Add summary stats to the parsed result."""
    txs = result.get("transactions", [])

    total_debit = sum(t["debit"] for t in txs)
    total_credit = sum(t["credit"] for t in txs)

    # Category breakdown
    category_totals: dict[str, float] = {}
    for t in txs:
        cat = t.get("category", "other")
        category_totals[cat] = category_totals.get(cat, 0.0) + t["debit"]

    # Monthly breakdown
    monthly: dict[str, dict[str, float]] = {}
    for t in txs:
        ym = t["date"][:7]  # "YYYY-MM"
        if ym not in monthly:
            monthly[ym] = {"debit": 0.0, "credit": 0.0}
        monthly[ym]["debit"] += t["debit"]
        monthly[ym]["credit"] += t["credit"]

    hdr = result.get("header", {})

    result["summary"] = {
        "total_transactions": len(txs),
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "net": round(total_credit - total_debit, 2),
        "opening_balance": hdr.get("opening_balance"),
        "current_balance": hdr.get("current_balance"),
        "category_breakdown": {k: round(v, 2) for k, v in category_totals.items()},
        "monthly_breakdown": {
            k: {"debit": round(v["debit"], 2), "credit": round(v["credit"], 2)}
            for k, v in sorted(monthly.items())
        },
    }

    return result
