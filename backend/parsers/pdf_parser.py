"""
High-Accuracy Multi-Strategy PDF Bank Statement Parser.
Tuned for Indian and international bank statements (Indian Bank, HDFC, SBI, ICICI, Axis, Kotak, PNB, Canara, etc.).
Features:
  - Universal Date, Amount, and Account metadata extraction.
  - Automatic detection of Bank Name and IFSC Code.
  - Multi-page table extraction with persistent column mapping across pages.
  - Multi-line transaction block parser for borderless/wrapped PDF statements.
  - Clean separation of transaction narration without truncation at internal hyphens.
  - Accurate token-based amount line parsing (Debit, Credit, Balance).
  - Mathematical balance verification and chronological reconciliation.
  - 100% Offline operation.
"""
from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Optional

import pdfplumber
import pypdf


class PasswordRequiredError(Exception):
    """Raised when a PDF is password protected and no password was provided."""
    pass


class InvalidPasswordError(Exception):
    """Raised when the provided password cannot decrypt the PDF."""
    pass

# ─── Date patterns ─────────────────────────────────────────────────────────────
_DATE_REGEX_STR = (
    r"(?:\d{1,2}[-/\.\s]+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[-/\.\s]+\d{2,4}"
    r"|\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}"
    r"|\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})"
)
_DATE_REGEX = re.compile(r"\b(" + _DATE_REGEX_STR + r")\b", re.I)

_DATE_FORMATS = [
    "%d %b %Y", "%d %B %Y", "%d %b %y",
    "%d-%b-%Y", "%d-%b-%y", "%d-%B-%Y", "%d-%B-%y",
    "%d/%b/%Y", "%d/%b/%y", "%d/%B/%Y", "%d/%B/%y",
    "%d.%b.%Y", "%d.%b.%y", "%d.%B.%Y", "%d.%B.%y",
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
    "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d",
    "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y",
    "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",
]

_CATEGORY_MAP = {
    "food": ["swiggy", "zomato", "restaurant", "food", "cafe", "domino", "mcdonald", "kfc", "pizza", "starbucks", "bake", "eats", "dine", "hotel", "canteen"],
    "shopping": ["amazon", "flipkart", "myntra", "ajio", "nykaa", "shopping", "mall", "store", "retail", "blinkit", "zepto", "instamart", "dmart", "reliancedigital", "croma"],
    "utilities": ["electricity", "water", "gas", "internet", "broadband", "airtel", "jio", "vi ", "bsnl", "recharge", "bescom", "tneb", "bill", "tatasky", "dish tv"],
    "transport": ["uber", "ola", "rapido", "metro", "petrol", "fuel", "irctc", "railway", "bus", "toll", "fastag", "shell", "hpcl", "bpcl", "indianoil", "auto"],
    "health": ["hospital", "pharmacy", "medplus", "apollo", "clinic", "doctor", "medical", "1mg", "pharmeasy", "health", "dental", "dr."],
    "entertainment": ["netflix", "prime", "hotstar", "spotify", "youtube", "pvr", "inox", "cinema", "movie", "play", "game", "bookmyshow"],
    "finance": ["emi", "loan", "insurance", "sip", "mutual fund", "fd", "neft", "imps", "rtgs", "lic", "groww", "zerodha", "tax", "charge", "interest", "chg", "fee", "gst"],
    "atm": ["atm", "cash withdrawal", "nfs", "cash wdl", "atm wdl", "self wdl"],
    "salary": ["salary", "payroll", "wages", "stipend"],
    "upi": ["upi", "gpay", "phonepe", "paytm", "bhim", "cred"],
}

_IFSC_BANK_MAP = {
    "SBIN": "State Bank of India",
    "HDFC": "HDFC Bank",
    "ICIC": "ICICI Bank",
    "IDIB": "Indian Bank",
    "UTIB": "Axis Bank",
    "KKBK": "Kotak Mahindra Bank",
    "PUNB": "Punjab National Bank",
    "CNRB": "Canara Bank",
    "BARB": "Bank of Baroda",
    "UBIN": "Union Bank of India",
    "BKID": "Bank of India",
    "IBKL": "IDBI Bank",
    "IOBA": "Indian Overseas Bank",
    "CBIN": "Central Bank of India",
    "UCBA": "UCO Bank",
    "YESB": "Yes Bank",
    "INDB": "IndusInd Bank",
    "FDRL": "Federal Bank",
}

_KNOWN_BANKS = [
    ("State Bank of India", ["state bank of india", "sbi"]),
    ("HDFC Bank", ["hdfc bank", "hdfc"]),
    ("ICICI Bank", ["icici bank", "icici"]),
    ("Indian Bank", ["indian bank"]),
    ("Axis Bank", ["axis bank", "axis"]),
    ("Kotak Mahindra Bank", ["kotak mahindra", "kotak"]),
    ("Punjab National Bank", ["punjab national bank", "pnb"]),
    ("Canara Bank", ["canara bank"]),
    ("Bank of Baroda", ["bank of baroda", "bob"]),
    ("Union Bank of India", ["union bank of india", "union bank"]),
    ("Bank of India", ["bank of india"]),
    ("IndusInd Bank", ["indusind"]),
    ("Yes Bank", ["yes bank"]),
    ("Federal Bank", ["federal bank"]),
    ("IDBI Bank", ["idbi bank", "idbi"]),
    ("Central Bank of India", ["central bank of india"]),
    ("Indian Overseas Bank", ["indian overseas bank", "iob"]),
    ("UCO Bank", ["uco bank"]),
]


def _parse_date(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    cleaned = re.sub(r"[^\w\s/.-]", " ", str(text)).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    m = _DATE_REGEX.search(cleaned)
    if m:
        sub = m.group(1).strip()
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(sub, fmt)
            except ValueError:
                continue
    return None


def _extract_amount(text: Optional[str]) -> Optional[float]:
    """Extract clean float amount from text."""
    amt, _ = _extract_amount_and_hint(text)
    return amt


def _extract_amount_and_hint(text: Optional[str]) -> tuple[Optional[float], Optional[str]]:
    """
    Extract clean absolute float amount and type hint ('debit', 'credit', or None).
    Handles:
      - Indian currency comma grouping: 1,25,000.00
      - Currency symbols: Rs., Rs, INR, ₹, $, etc.
      - Dr/Cr suffixes: 540.00 Dr, 125000.00 Cr, 500.00(Dr), 500.00(Cr)
      - Negative/Parenthesis signs: -500.00, (500.00) -> debit
      - Empty placeholders: -, --, nil, null, none, "" -> 0.0, None
    """
    if text is None:
        return None, None
    s = str(text).strip()
    if s in ("-", "--", "---", "nil", "null", "none", "", "."):
        return 0.0, None

    hint = None
    if re.search(r"\b(cr|credit|deposit)\b|\(cr\)", s, re.I):
        hint = "credit"
    elif re.search(r"\b(dr|debit|withdrawal)\b|\(dr\)", s, re.I):
        hint = "debit"
    elif s.startswith("-") or (s.startswith("(") and s.endswith(")")):
        hint = "debit"
    elif s.startswith("+"):
        hint = "credit"

    cleaned = (
        s.replace(",", "")
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .replace("INR", "")
        .replace("$", "")
        .replace("EUR", "")
        .replace("£", "")
        .strip()
    )

    m = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if m:
        try:
            return abs(float(m.group())), hint
        except ValueError:
            pass
    return None, hint


def _categorise(description: str) -> str:
    if not description:
        return "other"
    lower = description.lower()
    for category, keywords in _CATEGORY_MAP.items():
        for kw in keywords:
            if kw in lower:
                return category
    return "other"


def _detect_transaction_type(
    text: str = "",
    debit: Optional[float] = None,
    credit: Optional[float] = None,
    amount: Optional[float] = None,
    type_str: Optional[str] = None,
    prev_balance: Optional[float] = None,
    balance: Optional[float] = None,
    is_reverse: bool = False,
) -> str:
    """
    Robustly determine whether a transaction is 'debit' or 'credit'.
    Prioritizes explicit columns, then explicit indicators, then balance delta, then narration keywords.
    """
    # 1. Explicit debit / credit amounts
    if credit is not None and credit > 0 and (debit is None or debit == 0):
        return "credit"
    if debit is not None and debit > 0 and (credit is None or credit == 0):
        return "debit"

    # 2. Explicit type string (from 'Type' or 'Dr/Cr' column)
    if type_str:
        ts = str(type_str).strip().lower()
        if any(k in ts for k in ["cr", "credit", "deposit", "dep", "+"]):
            return "credit"
        if any(k in ts for k in ["dr", "debit", "withdrawal", "wdl", "-"]):
            return "debit"

    # 3. Explicit hint in text (e.g. '(Cr)', '(Dr)', ' Cr', ' Dr')
    if text:
        if re.search(r"\b(cr|credit)\b|\(cr\)", text, re.I):
            return "credit"
        if re.search(r"\b(dr|debit)\b|\(dr\)", text, re.I):
            return "debit"

    # 4. Running Balance Delta (Mathematical precision)
    if balance is not None and prev_balance is not None:
        delta = round(balance - prev_balance, 2) if not is_reverse else round(prev_balance - balance, 2)
        if delta > 0.001:
            return "credit"
        if delta < -0.001:
            return "debit"

    # 5. Narration keyword heuristics
    lower = (text or "").lower()
    credit_keywords = [
        "salary", "credited", "deposit", "interest", "refund", "dividend",
        "reversal", "reversed", "cash deposit", "by transfer", "transfer from",
        "neft cr", "imps cr", "rtgs cr", "upi/cr", "cashback", "subsidy", "bonus",
    ]
    debit_keywords = [
        "withdrawal", "wdl", "atm", "pos", "purchase", "swiggy", "zomato",
        "uber", "ola", "amazon", "flipkart", "bill", "charge", "fee", "tax",
        "gst", "rent", "insurance", "emi", "sip", "transfer to", "to transfer",
        "neft dr", "imps dr", "rtgs dr", "upi/dr", "paid to",
    ]
    if any(k in lower for k in credit_keywords):
        return "credit"
    if any(k in lower for k in debit_keywords):
        return "debit"

    return "debit"


def _parse_page_header(full_text: str) -> dict:
    """
    Extract account holder name, account number, IFSC code, bank name,
    statement period, opening balance, and ending/current balance from text.
    """
    result = {
        "account_holder": None,
        "account_number": None,
        "bank_name": None,
        "ifsc": None,
        "statement_from": None,
        "statement_to": None,
        "opening_balance": None,
        "current_balance": None,
    }

    # 0. IFSC Code Detection (Indian Banking Standard: 4 letters, 0, 6 alphanumeric)
    ifsc_m = re.search(r"\bIFSC(?:\s*Code)?[\s:]*([A-Z]{4}0[A-Z0-9]{6})\b", full_text, re.I)
    if not ifsc_m:
        ifsc_m = re.search(r"\b([A-Z]{4}0[A-Z0-9]{6})\b", full_text)
    if ifsc_m:
        result["ifsc"] = ifsc_m.group(1).strip().upper()
        # Direct bank name identification from IFSC code
        code_prefix = result["ifsc"][:4]
        if code_prefix in _IFSC_BANK_MAP:
            result["bank_name"] = _IFSC_BANK_MAP[code_prefix]

    # 0.1 Bank Name Detection from text if IFSC didn't resolve
    if not result["bank_name"]:
        top_lines = "\n".join(full_text.split("\n")[:25]).lower()
        for bank_name, aliases in _KNOWN_BANKS:
            if any(alias in top_lines for alias in aliases):
                result["bank_name"] = bank_name
                break

    # 1. Account Holder Name
    # 1.1 Compare if text contains salutations (Mr, Mrs, Ms, Dr, Shri, Smt, Master, etc.)
    salutation_m = re.search(
        r"\b((?:Mr|Mrs|Ms|Miss|Dr|Prof|Shri|Sri|Smt|Master|M/s)\.?\s+[A-Za-z][A-Za-z\s\.]{2,40}?)(?=\s*(?:\n|\r|Account|A/C|Customer|Address|Branch|IFSC|Phone|Mobile|CIF|,|\d{4,}|$))",
        full_text[:4000],
        re.I,
    )
    if salutation_m:
        cand = re.sub(r"\s+", " ", salutation_m.group(1)).strip().rstrip(".,;:-")
        if not any(k in cand.lower() for k in ["bank", "statement", "account", "branch", "balance", "opening", "closing", "period"]):
            result["account_holder"] = cand

    # 1.2 Fallback to labeled patterns (Account Holder Name, Customer Name, etc.)
    if not result["account_holder"]:
        name_patterns = [
            r"(?:Primary\s+)?Account\s*Holder(?:\s*(?:'s)?\s*Name)?[\s:]+([A-Za-z\s\.]+?)(?=\s*(?:Account\s*Type|Account\s*No|Account\s*Number|Customer|Branch|Address|IFSC|Nomination|\n|$))",
            r"Customer\s*Name[\s:]+([A-Za-z\s\.]+?)(?=\s*(?:Account|Customer|Branch|Address|IFSC|\n|$))",
            r"Name\s*of\s*(?:the\s*)?(?:Account\s*Holder|Customer)[\s:]+([A-Za-z\s\.]+?)(?=\s*(?:Account|Branch|Address|\n|$))",
            r"(?:Statement\s+of\s+Account\s*[:\-]\s*|Account\s+of\s*[:\-]\s*)([A-Za-z\s\.]+?)(?=\n|$)",
            r"(?:Name)[\s:]+([A-Z][A-Za-z\s\.]{2,35})(?=\n|$)",
        ]
        for pat in name_patterns:
            m = re.search(pat, full_text, re.I)
            if m:
                cand = re.sub(r"\s+", " ", m.group(1)).strip().rstrip(".,;:-")
                if len(cand) >= 3 and not any(k in cand.lower() for k in ["period", "statement", "account", "balance", "date", "branch", "type", "details"]):
                    result["account_holder"] = cand
                    break

    # 1.3 Uppercase line heuristic in top 25 lines
    if not result["account_holder"]:
        skip_words = [
            "bank", "statement", "account", "branch", "date", "ifsc", "rtgs",
            "period", "balance", "opening", "closing", "page", "from", "to",
            "summary", "address", "phone", "email", "total", "nomination",
            "micr", "cif", "pan", "gstin", "currency", "inr", "savings", "current",
            "activity", "details", "transaction", "description", "debits", "credits"
        ]
        for line in full_text.split("\n")[:25]:
            words = line.strip().split()
            if 2 <= len(words) <= 4 and all(w.isupper() for w in words if w.isalpha()):
                if not any(k in line.lower() for k in skip_words):
                    result["account_holder"] = line.strip()
                    break

    # 2. Account Number
    acct_patterns = [
        r"(?:account|a/c|acct|sb\s+a/c|ca\s+a/c|od\s+a/c)\s*(?:no\.?|num\.?|number|#|id)?[\s:]*([0-9A-Z*X-]{6,25})",
        r"Account\s*Number[\s:]+(\d{6,25})",
        r"(?:a/c\s*(?:no\.?|number)?|acct\s*#)[\s:]*([0-9A-Z*X-]{6,25})",
    ]
    for pat in acct_patterns:
        acct_m = re.search(pat, full_text, re.I)
        if acct_m:
            val = acct_m.group(1).strip()
            if re.search(r"\d", val) and val.lower() not in ("number", "account", "holder", "details"):
                result["account_number"] = val
                break

    # 3. Statement Period
    period_patterns = [
        r"(?:For\s*period|Statement\s*period|Period|Txn\s*Period)[\s:]*(" + _DATE_REGEX_STR + r")\s*[-–to]+\s*(" + _DATE_REGEX_STR + r")",
        r"(?:From\s*Date|From)[\s:]*(" + _DATE_REGEX_STR + r")\s*(?:To\s*Date|To)[\s:]*(" + _DATE_REGEX_STR + r")",
        r"(?:Statement\s+for\s+the\s+period\s+from)[\s:]*(" + _DATE_REGEX_STR + r")\s*[-–to]+\s*(" + _DATE_REGEX_STR + r")",
    ]
    for p_pat in period_patterns:
        period_m = re.search(p_pat, full_text, re.I)
        if period_m:
            from_dt = _parse_date(period_m.group(1))
            to_dt = _parse_date(period_m.group(2))
            result["statement_from"] = from_dt.strftime("%Y-%m-%d") if from_dt else period_m.group(1).strip()
            result["statement_to"] = to_dt.strftime("%Y-%m-%d") if to_dt else period_m.group(2).strip()
            break

    # 4. Opening Balance
    open_bal_patterns = [
        r"(?:opening\s*bal(?:ance)?|brought\s*forward|b/f)(?:\s+(?:as\s+on|as\s+of|on)\s+[^\n:]+)?[\s:₹Rs.INR]*([0-9,]+(?:\.\d{1,2})?)\s*(cr|dr)?",
        r"opening\s*bal(?:ance)?[\s:₹Rs.INR]*([0-9,]+(?:\.\d{1,2})?)",
    ]
    for ob_pat in open_bal_patterns:
        open_bal_m = re.search(ob_pat, full_text, re.I)
        if open_bal_m:
            val = _extract_amount(open_bal_m.group(1))
            if val is not None:
                if open_bal_m.lastindex >= 2 and open_bal_m.group(2) and open_bal_m.group(2).lower() == "dr":
                    val = -val
                result["opening_balance"] = val
                break

    # 5. Current / Closing / Ending Balance (Explicitly requires closing/ending/available keyword to avoid matching opening balance)
    end_bal_patterns = [
        r"(?:ending|closing|available|current|clear|ledger|effective\s+available|net\s+available)\s*bal(?:ance)?(?:\s+(?:as\s+on|as\s+of|on)\s+[^\n:]+)?[\s:₹Rs.INR]*([0-9,]+(?:\.\d{1,2})?)\s*(cr|dr)?",
        r"(?<!opening\s)(?<!opening\s\s)\bbal(?:ance)?\s+(?:as\s+on|as\s+of|on)\s+[^\n:]+[\s:₹Rs.INR]*([0-9,]+(?:\.\d{1,2})?)\s*(cr|dr)?",
    ]
    for eb_pat in end_bal_patterns:
        end_bal_m = re.search(eb_pat, full_text, re.I)
        if end_bal_m:
            val = _extract_amount(end_bal_m.group(1))
            if val is not None:
                if end_bal_m.lastindex >= 2 and end_bal_m.group(2) and end_bal_m.group(2).lower() == "dr":
                    val = -val
                result["current_balance"] = val
                break

    return result


def _is_header_row(row: list) -> bool:
    if not row:
        return False
    joined = " ".join(str(c) for c in row if c).lower()
    keywords = [
        "date", "particulars", "description", "narration", "details",
        "debits", "credits", "debit", "credit", "withdrawal", "deposit",
        "balance", "txn", "amount", "dr", "cr"
    ]
    matches = sum(1 for k in keywords if re.search(r"\b" + k + r"\b", joined))
    return matches >= 2


def _detect_col_map(header_row: list) -> dict:
    col_map = {}
    for i, cell in enumerate(header_row):
        if not cell:
            continue
        text = str(cell).lower().replace("\n", " ").strip()
        # Date column
        if re.search(r"\b(date|txn\s*date|transaction\s*date|trans\s*date|value\s*date)\b", text) and "date" not in col_map:
            col_map["date"] = i
        # Description / Narration
        elif re.search(r"\b(narration|particulars|description|transaction\s*details|details|remarks|memo)\b", text) and "description" not in col_map:
            col_map["description"] = i
        # Debit / Withdrawal
        elif re.search(r"\b(debits?|withdrawals?|dr\b|dr\.|debit\s*amt|withdrawal\s*amt|paid\s*out|money\s*out)\b", text) and "debit" not in col_map:
            col_map["debit"] = i
        # Credit / Deposit
        elif re.search(r"\b(credits?|deposits?|cr\b|cr\.|credit\s*amt|deposit\s*amt|paid\s*in|money\s*in)\b", text) and "credit" not in col_map:
            col_map["credit"] = i
        # Single Amount column
        elif re.search(r"\b(amount|txn\s*amt|transaction\s*amount|net\s*amount)\b", text) and "amount" not in col_map:
            col_map["amount"] = i
        # Balance column
        elif re.search(r"\b(balance|closing\s*bal|closing|available\s*bal|ledger\s*bal|bal\b)\b", text) and "balance" not in col_map:
            col_map["balance"] = i
        # Type (Dr/Cr) column
        elif re.search(r"\b(type|dr/cr|cr/dr|dr\s*/\s*cr|tran\s*type|txn\s*type)\b", text) and "type" not in col_map:
            col_map["type"] = i

    return col_map


def _parse_row_from_columns(row: list, col_map: dict) -> Optional[dict]:
    def get(key):
        idx = col_map.get(key)
        if idx is not None and idx < len(row):
            val = str(row[idx]).strip() if row[idx] is not None else None
            return val
        return None

    date_str = get("date")
    if not date_str:
        return None

    parsed_date = _parse_date(date_str)
    if not parsed_date:
        return None

    description = (get("description") or "").replace("\n", " ").strip()
    if not description:
        description = "Transaction"

    debit_raw = get("debit")
    credit_raw = get("credit")
    amount_raw = get("amount")
    type_raw = get("type")
    balance_raw = get("balance")

    debit = None
    credit = None
    balance = None

    if balance_raw is not None:
        bal_val, bal_hint = _extract_amount_and_hint(balance_raw)
        if bal_val is not None:
            balance = -bal_val if bal_hint == "debit" else bal_val

    # Case 1: Separate Debit & Credit columns
    if "debit" in col_map or "credit" in col_map:
        d_val, d_hint = _extract_amount_and_hint(debit_raw)
        c_val, c_hint = _extract_amount_and_hint(credit_raw)

        debit = d_val if d_val is not None else 0.0
        credit = c_val if c_val is not None else 0.0

        if debit > 0 and credit == 0:
            tx_type = "debit"
        elif credit > 0 and debit == 0:
            tx_type = "credit"
        elif debit == 0 and credit == 0:
            return None
        else:
            tx_type = _detect_transaction_type(description, debit=debit, credit=credit, type_str=type_raw)
    # Case 2: Single Amount column with optional Type column
    elif amount_raw is not None:
        amt_val, amt_hint = _extract_amount_and_hint(amount_raw)
        if amt_val is None or amt_val == 0:
            return None

        tx_type = amt_hint or _detect_transaction_type(
            description,
            amount=amt_val,
            type_str=type_raw,
        )
        if tx_type == "credit":
            credit = amt_val
            debit = 0.0
        else:
            debit = amt_val
            credit = 0.0
    else:
        return None

    return {
        "date": parsed_date.strftime("%Y-%m-%d"),
        "description": description,
        "debit": debit or 0.0,
        "credit": credit or 0.0,
        "balance": balance,
        "type": tx_type,
        "category": _categorise(description),
    }


def _extract_tables_from_pdf(pdf) -> list[dict]:
    """Strategy 1 & 2: Multi-Page Table Extractor with persistent cross-page column mapping."""
    transactions = []

    for strategy in [{}, {"vertical_strategy": "text", "horizontal_strategy": "text"}]:
        if transactions:
            break

        active_col_map = {}
        last_row_len = None

        for page in pdf.pages:
            try:
                tables = page.extract_tables(strategy) if strategy else page.extract_tables()
            except Exception:
                continue

            for table in tables or []:
                if not table:
                    continue

                for row in table:
                    if not row or not any(row):
                        continue

                    # Check if this row is a table header
                    if _is_header_row(row):
                        detected = _detect_col_map(row)
                        if detected.get("date") is not None:
                            active_col_map = detected
                            last_row_len = len(row)
                        continue

                    if not active_col_map:
                        continue

                    # Parse row if column count matches
                    if last_row_len and abs(len(row) - last_row_len) <= 1:
                        tx = _parse_row_from_columns(row, active_col_map)
                        if tx:
                            transactions.append(tx)

    return transactions


def _extract_transactions_from_text(full_text: str, opening_balance: Optional[float] = None) -> list[dict]:
    """
    Strategy 3: Multi-Line Transaction Block Parser.
    Handles wrapped statements (Indian Bank, SBI, HDFC, ICICI, etc.) with:
      - Line starting with Date
      - Wrapped narration without truncating hyphens
      - Token-based amount line parsing (Debit, Credit, Balance)
      - Mathematical running balance reconciliation
    """
    lines = full_text.split("\n")
    blocks = []
    current_block = []
    in_activity = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower()

        # Start of activity
        if any(h in lower for h in [
            "account activity", "transaction details", "txn date", "date narration",
            "particulars", "statement of account", "transaction history"
        ]):
            in_activity = True
            continue

        if not in_activity:
            if re.match(r"^\s*" + _DATE_REGEX_STR, stripped, re.I) and re.search(r"\d+\.\d{2}", stripped):
                in_activity = True
            else:
                continue

        # Skip final totals / summary lines at the very end
        if lower.startswith("ending balance") or lower.startswith("account summary"):
            if current_block:
                blocks.append(current_block)
                current_block = []
            break

        # Check if line begins with a Date
        date_match = re.match(r"^\s*(" + _DATE_REGEX_STR + r")", stripped, re.I)
        if date_match:
            if current_block:
                blocks.append(current_block)
            current_block = [stripped]
        elif current_block:
            current_block.append(stripped)

    if current_block:
        blocks.append(current_block)

    transactions = []
    prev_balance = opening_balance

    # Regex for lines that actually contain financial amount columns (2+ amounts, or dash + amount, or amount + dash)
    is_amt_line_pat = re.compile(
        r"(?:-\s*(?:INR|Rs\.?|₹|\$)?\s*[0-9,]+(?:\.\d{2})?|[0-9,]+(?:\.\d{2})?\s*-\s*|(?:[0-9,]+\.\d{2}.*){2,})",
        re.I,
    )
    # Currency-prefixed amount pattern at line end (prioritized over bare numbers)
    curr_amt_pat = re.compile(
        r"(?:(?:[-–—]\s*)?(?:INR|Rs\.?|₹|\$)\s*[0-9,]+(?:\.\d{2})?.*)$",
        re.I,
    )
    # Regex for trailing amounts on a line (whitespace boundary before first amount)
    amt_trailing_pat = re.compile(
        r"(?:(?<=\s)|^)((?:(?:[-–—]|(?:INR|Rs\.?|₹|\$)\s*)?\s*[0-9,]+(?:\.\d{2})?\s*|[-–—]\s*)+)$",
        re.I,
    )

    for block in blocks:
        date_m = re.match(r"^\s*(" + _DATE_REGEX_STR + r")", block[0], re.I)
        if not date_m:
            continue
        date_str = date_m.group(1)
        parsed_date = _parse_date(date_str)
        if not parsed_date:
            continue

        amt_tokens = []
        narration_parts = []

        for line in block:
            cleaned = line.strip()
            # Strip date from start if on first line
            no_date = re.sub(r"^\s*" + _DATE_REGEX_STR, "", cleaned, flags=re.I).strip()

            if is_amt_line_pat.search(cleaned):
                m_curr = curr_amt_pat.search(no_date)
                m_amt = m_curr or amt_trailing_pat.search(no_date)
                if m_amt:
                    desc_part = no_date[:m_amt.start()].strip()
                    amt_str = m_amt.group(0).strip() if m_curr else m_amt.group(1).strip()
                    if desc_part:
                        narration_parts.append(desc_part)

                    # Tokenize amount string into dashes and float numbers
                    cleaned_amt = (
                        amt_str.replace("Rs.", " ")
                        .replace("Rs", " ")
                        .replace("INR", " ")
                        .replace("₹", " ")
                        .replace("$", " ")
                    )
                    tokens = []
                    for t_match in re.finditer(
                        r"(?:(?<=\s)|^)[-–—](?=\s|$)|(?:\b|[-+])\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?\b|\b\d+(?:\.\d{1,2})?\b",
                        cleaned_amt,
                    ):
                        t = t_match.group(0).strip()
                        if t in ("-", "–", "—"):
                            tokens.append("-")
                        else:
                            try:
                                tokens.append(float(t.replace(",", "")))
                            except ValueError:
                                pass

                    if tokens and not amt_tokens:
                        amt_tokens = tokens
                else:
                    if no_date:
                        narration_parts.append(no_date)
            else:
                if no_date:
                    narration_parts.append(no_date)

        narration = " ".join(narration_parts).strip() or "Transaction"

        debit = 0.0
        credit = 0.0
        balance = None

        # Resolve amounts from tokens (using right-to-left indexing for robustness against narration numbers)
        # Case 1: [..., debit_amt, '-', balance] -> Debit
        if len(amt_tokens) >= 3 and amt_tokens[-2] == "-" and isinstance(amt_tokens[-1], float) and isinstance(amt_tokens[-3], float):
            debit = amt_tokens[-3]
            balance = amt_tokens[-1]
        # Case 2: [..., '-', credit_amt, balance] -> Credit
        elif len(amt_tokens) >= 3 and amt_tokens[-3] == "-" and isinstance(amt_tokens[-1], float) and isinstance(amt_tokens[-2], float):
            credit = amt_tokens[-2]
            balance = amt_tokens[-1]
        # Case 3: [..., debit_amt, credit_amt, balance]
        elif len(amt_tokens) >= 3 and all(isinstance(x, float) for x in amt_tokens[-3:]):
            debit = amt_tokens[-3]
            credit = amt_tokens[-2]
            balance = amt_tokens[-1]
        # Case 4: [..., amt, balance]
        elif len(amt_tokens) >= 2 and all(isinstance(x, float) for x in amt_tokens[-2:]):
            amt, balance = amt_tokens[-2], amt_tokens[-1]
            if prev_balance is not None:
                diff = round(balance - prev_balance, 2)
                if diff > 0:
                    credit = diff
                else:
                    debit = abs(diff)
            else:
                tx_type = _detect_transaction_type(narration, amount=amt)
                if tx_type == "credit":
                    credit = amt
                else:
                    debit = amt
        # Case 5: [single amount]
        elif len(amt_tokens) >= 1 and isinstance(amt_tokens[-1], float):
            amt = amt_tokens[-1]
            tx_type = _detect_transaction_type(narration, amount=amt)
            if tx_type == "credit":
                credit = amt
            else:
                debit = amt

        # Running balance mathematical verification
        if balance is not None and prev_balance is not None:
            expected_diff = round(balance - prev_balance, 2)
            if expected_diff > 0 and (debit == 0 and credit == 0):
                credit = expected_diff
                debit = 0.0
            elif expected_diff < 0 and (debit == 0 and credit == 0):
                debit = abs(expected_diff)
                credit = 0.0

        if balance is not None:
            prev_balance = balance

        tx_type = "credit" if credit > 0 and debit == 0 else "debit"

        transactions.append({
            "date": parsed_date.strftime("%Y-%m-%d"),
            "description": narration,
            "debit": debit,
            "credit": credit,
            "balance": balance,
            "type": tx_type,
            "category": _categorise(narration),
        })

    return transactions


def _decrypt_pdf_if_needed(file_bytes: bytes, password: Optional[str] = None) -> bytes:
    """
    Check if the PDF is encrypted. If encrypted:
      - Raise PasswordRequiredError if no password is provided.
      - Attempt decryption with the provided password.
      - If invalid, raise InvalidPasswordError.
      - If valid, return the decrypted PDF bytes.
    If not encrypted, returns file_bytes unchanged.
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    except Exception:
        # If pypdf cannot read or format is unencrypted raw, let downstream handle
        return file_bytes

    if not reader.is_encrypted:
        return file_bytes

    if not password:
        raise PasswordRequiredError(
            "This statement is password-protected. Please enter your password to unlock it."
        )

    res = reader.decrypt(password)
    # res is 0 on failure, 1 (USER) or 2 (OWNER) on success
    if res == 0:
        raise InvalidPasswordError(
            "Incorrect password. Please verify your password and try again."
        )

    # Write decrypted pages to a clean stream
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def parse_pdf(file_bytes: bytes, password: Optional[str] = None) -> dict:
    """
    Parse a PDF bank statement with multi-strategy fallback, automatic bank & IFSC detection,
    and mathematical balance verification. Supports password-protected statements.
    """
    clean_bytes = _decrypt_pdf_if_needed(file_bytes, password=password)
    full_text_pages = []
    transactions = []

    with pdfplumber.open(io.BytesIO(clean_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text_pages.append(text)

        # Strategy 1 & 2: Table Extractors
        transactions = _extract_tables_from_pdf(pdf)

    full_text = "\n".join(full_text_pages)
    header = _parse_page_header(full_text)
    opening_bal = header.get("opening_balance")

    # Strategy 3: Multi-Line Transaction Block Parser
    text_txs = _extract_transactions_from_text(full_text, opening_balance=opening_bal)

    # Pick the strategy that extracted more transactions or higher quality
    if len(text_txs) > len(transactions):
        transactions = text_txs
    elif text_txs and len(text_txs) == len(transactions):
        table_scored = sum(1 for t in transactions if t.get("balance") is not None and (t["debit"] > 0 or t["credit"] > 0))
        text_scored = sum(1 for t in text_txs if t.get("balance") is not None and (t["debit"] > 0 or t["credit"] > 0))
        if text_scored >= table_scored:
            transactions = text_txs

    # Detect Chronological Direction (Ascending vs Descending)
    if len(transactions) >= 2:
        first_date = transactions[0].get("date", "")
        last_date = transactions[-1].get("date", "")
        is_reverse = bool(first_date and last_date and first_date > last_date)
    else:
        is_reverse = False

    # Mathematical Cross-Verification: only resolve missing or zero debit/credit
    for i, t in enumerate(transactions):
        bal = t.get("balance")
        prev_bal = None
        if not is_reverse and i > 0:
            prev_bal = transactions[i - 1].get("balance")
        elif is_reverse and i < len(transactions) - 1:
            prev_bal = transactions[i + 1].get("balance")
        elif i == 0 and opening_bal is not None:
            prev_bal = opening_bal

        if bal is not None and prev_bal is not None:
            delta = round(bal - prev_bal, 2)
            if t["debit"] == 0 and t["credit"] == 0:
                if delta > 0:
                    t["type"] = "credit"
                    t["credit"] = delta
                    t["debit"] = 0.0
                elif delta < 0:
                    t["type"] = "debit"
                    t["debit"] = abs(delta)
                    t["credit"] = 0.0

    # Derive statement period from transaction dates if not detected
    if transactions:
        valid_dates = sorted(t["date"] for t in transactions if t.get("date"))
        if valid_dates:
            if not header.get("statement_from"):
                header["statement_from"] = valid_dates[0]
            if not header.get("statement_to"):
                header["statement_to"] = valid_dates[-1]

    # Derive current balance from latest transaction if not found in header
    if header.get("current_balance") is None and transactions:
        latest_tx = transactions[0] if is_reverse else transactions[-1]
        if latest_tx.get("balance") is not None:
            header["current_balance"] = latest_tx["balance"]
        else:
            search_txs = transactions if is_reverse else list(reversed(transactions))
            for tx in search_txs:
                if tx.get("balance") is not None:
                    header["current_balance"] = tx["balance"]
                    break

    # Derive opening balance from earliest transaction if not found in header
    if header.get("opening_balance") is None and transactions:
        earliest_tx = transactions[-1] if is_reverse else transactions[0]
        if earliest_tx.get("balance") is not None:
            bal = earliest_tx["balance"]
            deb = earliest_tx.get("debit", 0.0)
            cred = earliest_tx.get("credit", 0.0)
            header["opening_balance"] = round(bal - cred + deb, 2)

    return {"header": header, "transactions": transactions}
