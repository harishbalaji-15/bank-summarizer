"""
CSV / Excel Bank Statement Parser using pandas.
Supports 100% offline parsing of Indian and global bank statement exports (CSV, XLSX, XLS).
Features:
  - Multi-encoding support (utf-8-sig, utf-8, latin-1, cp1252).
  - Multi-delimiter auto-detection (comma, semicolon, tab).
  - Metadata / Preamble header extraction (Account Holder, Account Number, Period, Closing Balance).
  - Robust column role mapping (Date, Narration, Debit, Credit, Amount, Balance, Type).
  - Single Amount column reconciliation with Dr/Cr indicators or balance deltas.
  - Direction detection (ascending vs descending).
"""
from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Optional

import pandas as pd

from .pdf_parser import (
    _categorise,
    _detect_transaction_type,
    _extract_amount,
    _extract_amount_and_hint,
    _parse_date,
    _parse_page_header,
)


def _normalise_header(col: str) -> str:
    return str(col).lower().replace("\n", " ").strip()


def _map_columns(df: pd.DataFrame) -> dict:
    """Return a mapping of role -> column_name using smart keyword matching."""
    col_map: dict[str, str] = {}
    for col in df.columns:
        norm = _normalise_header(col)
        # Date
        if any(k in norm for k in [
            "date", "txn dt", "value dt", "txn date", "posting date",
            "trans date", "val date", "booking date", "post date"
        ]) and "date" not in col_map:
            col_map["date"] = col
        # Description / Narration
        elif any(k in norm for k in [
            "description", "narration", "particulars", "remarks", "details",
            "memo", "desc", "transaction details", "transaction remarks"
        ]) and "description" not in col_map:
            col_map["description"] = col
        # Debit
        elif (any(k in norm for k in [
            "debit", "withdrawal", "dr amount", "dr.", "dr amt", "withdraw",
            "paid out", "payments", "payment", "money out", "spent"
        ]) or norm == "dr") and "debit" not in col_map:
            col_map["debit"] = col
        # Credit
        elif (any(k in norm for k in [
            "credit", "deposit", "cr amount", "cr.", "cr amt", "received",
            "paid in", "receipts", "receipt", "money in"
        ]) or norm == "cr") and "credit" not in col_map:
            col_map["credit"] = col
        # Single Amount
        elif any(k in norm for k in ["amount", "txn amt", "transaction amount", "net amount", "amt"]) and "amount" not in col_map:
            col_map["amount"] = col
        # Balance
        elif any(k in norm for k in [
            "balance", "closing bal", "running bal", "available bal", "ledger bal", "bal"
        ]) and "balance" not in col_map:
            col_map["balance"] = col
        # Type
        elif any(k in norm for k in [
            "type", "dr/cr", "cr/dr", "dr / cr", "cr / dr", "transaction type", "tran type", "txn type"
        ]) and "type" not in col_map:
            col_map["type"] = col

    return col_map


def _cell_float_and_hint(val) -> tuple[Optional[float], Optional[str]]:
    if pd.isna(val) or val is None:
        return None, None
    s = str(val).strip()
    if s == "":
        return None, None
    return _extract_amount_and_hint(s)


def _parse_dataframe(df: pd.DataFrame) -> tuple[list[dict], dict]:
    """Convert a DataFrame into transactions and header information."""
    col_map = _map_columns(df)
    transactions: list[dict] = []

    if "date" not in col_map:
        return [], {}

    # Pre-parse rows
    raw_rows = []
    for _, row in df.iterrows():
        date_raw = str(row.get(col_map["date"], "")).strip()
        if not date_raw or date_raw.lower() in ("nan", "nat", "none"):
            continue

        parsed_date = _parse_date(date_raw)
        if not parsed_date:
            try:
                parsed_date = pd.to_datetime(date_raw, dayfirst=True)
            except Exception:
                continue

        description = str(row.get(col_map.get("description", ""), "") or "").strip()
        if description.lower() in ("nan", "none"):
            description = "Transaction"

        debit_amt, _ = _cell_float_and_hint(row.get(col_map["debit"])) if "debit" in col_map else (None, None)
        credit_amt, _ = _cell_float_and_hint(row.get(col_map["credit"])) if "credit" in col_map else (None, None)
        amount_amt, amount_hint = _cell_float_and_hint(row.get(col_map["amount"])) if "amount" in col_map else (None, None)
        balance_amt, _ = _cell_float_and_hint(row.get(col_map["balance"])) if "balance" in col_map else (None, None)
        type_str = str(row.get(col_map.get("type", ""), "") or "").strip()

        raw_rows.append({
            "parsed_date": parsed_date,
            "description": description,
            "debit_raw": debit_amt,
            "credit_raw": credit_amt,
            "amount_raw": amount_amt,
            "amount_hint": amount_hint,
            "balance_raw": balance_amt,
            "type_str": type_str,
        })

    if not raw_rows:
        return [], {}

    # Detect chronological direction
    first_dt = raw_rows[0]["parsed_date"]
    last_dt = raw_rows[-1]["parsed_date"]
    is_reverse = bool(first_dt and last_dt and first_dt > last_dt)

    for i, r in enumerate(raw_rows):
        debit = r["debit_raw"]
        credit = r["credit_raw"]
        amount = r["amount_raw"]
        balance = r["balance_raw"]
        type_str = r["type_str"]
        desc = r["description"]

        # Case 1: Separate Debit & Credit columns
        if debit is not None or credit is not None:
            deb_val = debit or 0.0
            cred_val = credit or 0.0
            if deb_val == 0 and cred_val == 0:
                continue

            tx_type = _detect_transaction_type(
                desc,
                debit=deb_val,
                credit=cred_val,
                type_str=type_str,
            )
            debit = deb_val
            credit = cred_val
        # Case 2: Single Amount column
        elif amount is not None and amount > 0:
            prev_bal = None
            if not is_reverse and i > 0:
                prev_bal = raw_rows[i - 1]["balance_raw"]
            elif is_reverse and i < len(raw_rows) - 1:
                prev_bal = raw_rows[i + 1]["balance_raw"]

            tx_type = r["amount_hint"] or _detect_transaction_type(
                desc,
                amount=amount,
                type_str=type_str,
                prev_balance=prev_bal,
                balance=balance,
                is_reverse=is_reverse,
            )
            if tx_type == "credit":
                credit = amount
                debit = 0.0
            else:
                debit = amount
                credit = 0.0
        else:
            continue

        transactions.append({
            "date": r["parsed_date"].strftime("%Y-%m-%d"),
            "description": desc,
            "debit": debit or 0.0,
            "credit": credit or 0.0,
            "balance": balance,
            "type": tx_type,
            "category": _categorise(desc),
        })

    header: dict = {
        "account_holder": None,
        "account_number": None,
        "bank_name": None,
        "ifsc": None,
        "statement_from": None,
        "statement_to": None,
        "opening_balance": None,
        "current_balance": None,
    }

    if transactions:
        sorted_dates = sorted(t["date"] for t in transactions if t.get("date"))
        if sorted_dates:
            header["statement_from"] = sorted_dates[0]
            header["statement_to"] = sorted_dates[-1]

        # Current / Ending Balance from latest transaction
        latest_tx = transactions[0] if is_reverse else transactions[-1]
        if latest_tx.get("balance") is not None:
            header["current_balance"] = latest_tx["balance"]
        else:
            search_list = transactions if is_reverse else list(reversed(transactions))
            for tx in search_list:
                if tx.get("balance") is not None:
                    header["current_balance"] = tx["balance"]
                    break

        # Opening balance from earliest transaction
        earliest_tx = transactions[-1] if is_reverse else transactions[0]
        if earliest_tx.get("balance") is not None:
            header["opening_balance"] = round(
                earliest_tx["balance"] - earliest_tx.get("credit", 0.0) + earliest_tx.get("debit", 0.0), 2
            )

    return transactions, header


def parse_csv(file_bytes: bytes) -> dict:
    """Parse a CSV bank statement with auto-delimiter and encoding fallback."""
    # 1. Extract preamble header info from first 30 lines
    preamble_header = {}
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            text_sample = file_bytes.decode(enc, errors="ignore")[:4000]
            preamble_header = _parse_page_header(text_sample)
            break
        except Exception:
            pass

    # 2. Try loading DataFrame by skipping variable metadata rows
    df = None
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        for skip in range(0, 25):
            for sep in [None, ",", ";", "\t"]:
                try:
                    candidate = pd.read_csv(
                        io.BytesIO(file_bytes),
                        skiprows=skip,
                        sep=sep,
                        engine="python",
                        encoding=enc,
                        on_bad_lines="skip",
                    )
                    col_map = _map_columns(candidate)
                    if "date" in col_map and (
                        "debit" in col_map or "credit" in col_map or "amount" in col_map or "description" in col_map
                    ):
                        df = candidate
                        break
                except Exception:
                    continue
            if df is not None:
                break
        if df is not None:
            break

    if df is None:
        # Fallback to standard read
        df = pd.read_csv(io.BytesIO(file_bytes), on_bad_lines="skip", engine="python")

    df.dropna(how="all", inplace=True)
    transactions, header = _parse_dataframe(df)

    # Merge preamble headers
    for k, v in preamble_header.items():
        if v is not None and not header.get(k):
            header[k] = v

    return {"header": header, "transactions": transactions}


def parse_excel(file_bytes: bytes) -> dict:
    """Parse an Excel bank statement (.xlsx / .xls)."""
    xl = pd.ExcelFile(io.BytesIO(file_bytes))
    all_transactions: list[dict] = []
    header: dict = {}

    for sheet_name in xl.sheet_names:
        for skip in range(0, 25):
            try:
                candidate = xl.parse(sheet_name, skiprows=skip)
                col_map = _map_columns(candidate)
                if "date" in col_map and (
                    "debit" in col_map or "credit" in col_map or "amount" in col_map or "description" in col_map
                ):
                    candidate.dropna(how="all", inplace=True)
                    txs, hdr = _parse_dataframe(candidate)
                    if txs:
                        all_transactions.extend(txs)
                        if not header:
                            header = hdr
                        break
            except Exception:
                continue

    return {"header": header, "transactions": all_transactions}
