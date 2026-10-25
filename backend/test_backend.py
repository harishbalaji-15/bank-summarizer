"""
Quick smoke-test for the backend.
Run after starting the backend with: python main.py

Usage:
    python test_backend.py
    python test_backend.py path/to/statement.pdf
"""
import sys
import json
import urllib.request
import urllib.parse

BASE = "http://localhost:8000"


def test_health():
    with urllib.request.urlopen(f"{BASE}/health", timeout=3) as r:
        data = json.loads(r.read())
    assert data["status"] == "ok", f"Unexpected: {data}"
    print("[OK] /health OK")


def test_parse(filepath: str):
    import mimetypes
    mime, _ = mimetypes.guess_type(filepath)
    mime = mime or "application/octet-stream"
    filename = filepath.split("\\")[-1].split("/")[-1]

    boundary = "----PythonBoundary"
    with open(filepath, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE}/api/parse",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.loads(r.read())

    header = result.get("header", {})
    txs = result.get("transactions", [])
    summary = result.get("summary", {})

    print(f"\n[PARSED] {filename}")
    print(f"   Account Holder : {header.get('account_holder') or '-'}")
    print(f"   Account Number : {header.get('account_number') or '-'}")
    print(f"   Period         : {header.get('statement_from') or '-'} -> {header.get('statement_to') or '-'}")
    print(f"   Balance        : {header.get('current_balance') or '-'}")
    print(f"\n[SUMMARY]")
    print(f"   Transactions   : {summary.get('total_transactions', 0)}")
    print(f"   Total Debit    : Rs. {summary.get('total_debit', 0):,.2f}")
    print(f"   Total Credit   : Rs. {summary.get('total_credit', 0):,.2f}")
    print(f"   Net            : Rs. {summary.get('net', 0):,.2f}")

    cats = summary.get("category_breakdown", {})
    if cats:
        print(f"\n[CATEGORIES]")
        for cat, amt in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"   {cat:<15} Rs. {amt:,.2f}")

    if txs:
        print(f"\n[TRANSACTIONS SAMPLE]")
        for tx in txs[:5]:
            sign = "-" if tx["type"] == "debit" else "+"
            amt = tx["debit"] if tx["type"] == "debit" else tx["credit"]
            print(f"   {tx['date']}  {sign}Rs.{amt:,.2f}  {tx['description'][:50]}")

    print(f"\n[OK] Parse succeeded ({len(txs)} transactions found)")


if __name__ == "__main__":
    test_health()
    if len(sys.argv) > 1:
        test_parse(sys.argv[1])
    else:
        import os
        sample = "sample_statement.pdf" if os.path.exists("sample_statement.pdf") else None
        if sample:
            test_parse(sample)
        else:
            print("\nTip: pass a statement file path to test parsing:")
            print("  python test_backend.py your_statement.pdf")
