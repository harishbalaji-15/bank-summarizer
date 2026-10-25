"""
Offline Comprehensive Test Suite for Bank Statement Parsers.
Tests PDF, CSV, Excel, and Indian Bank formats without requiring external networks.
Run: python test_parsers_offline.py
"""
import os
import io
import pandas as pd
from parsers.pdf_parser import parse_pdf, _parse_page_header, _extract_transactions_from_text
from parsers.csv_excel_parser import parse_csv, parse_excel
import test_indian_bank

def test_hdfc_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), "sample_statement.pdf")
    with open(pdf_path, "rb") as f:
        data = f.read()
    res = parse_pdf(data)
    hdr = res["header"]
    txs = res["transactions"]

    print("\n--- TEST: HDFC Sample PDF ---")
    print(f"Holder       : {hdr.get('account_holder')}")
    print(f"Bank         : {hdr.get('bank_name')}")
    print(f"Account No   : {hdr.get('account_number')}")
    print(f"Period       : {hdr.get('statement_from')} to {hdr.get('statement_to')}")
    print(f"Opening Bal  : {hdr.get('opening_balance')}")
    print(f"Current Bal  : {hdr.get('current_balance')}")
    print(f"Transactions : {len(txs)}")

    assert hdr.get("account_holder") == "RAJESH SHARMA", "Account holder mismatch"
    assert hdr.get("account_number") == "501004928172", "Account number mismatch"
    assert hdr.get("bank_name") == "HDFC Bank", "Bank name mismatch"
    assert hdr.get("current_balance") == 93341.0, "Current balance mismatch"
    assert len(txs) == 13, f"Expected 13 transactions, got {len(txs)}"

    tot_dr = sum(t["debit"] for t in txs)
    tot_cr = sum(t["credit"] for t in txs)
    assert tot_dr == 54133.0, f"Expected 54133.0 debits, got {tot_dr}"
    assert tot_cr == 125450.0, f"Expected 125450.0 credits, got {tot_cr}"
    print("[PASS] HDFC Sample PDF parsed perfectly!")

def test_indian_bank_ocr():
    ocr_text = test_indian_bank.full_ocr
    hdr = _parse_page_header(ocr_text)
    txs = _extract_transactions_from_text(ocr_text, hdr.get("opening_balance"))

    print("\n--- TEST: Indian Bank Format ---")
    print(f"Holder       : {hdr.get('account_holder')}")
    print(f"Bank         : {hdr.get('bank_name')}")
    print(f"IFSC         : {hdr.get('ifsc')}")
    print(f"Account No   : {hdr.get('account_number')}")
    print(f"Opening Bal  : {hdr.get('opening_balance')}")
    print(f"Current Bal  : {hdr.get('current_balance')}")
    print(f"Transactions : {len(txs)}")

    assert hdr.get("account_holder") == "USHA KUMAR", "Account holder mismatch"
    assert hdr.get("account_number") == "6032183663", "Account number mismatch"
    assert hdr.get("bank_name") == "Indian Bank", "Bank name mismatch"
    assert hdr.get("ifsc") == "IDIB000M038", "IFSC mismatch"
    assert hdr.get("opening_balance") == 1485.31, "Opening balance mismatch"
    assert hdr.get("current_balance") == 9771.85, "Current balance mismatch"
    assert len(txs) == 12, f"Expected 12 transactions, got {len(txs)}"

    tot_dr = sum(t["debit"] for t in txs)
    tot_cr = sum(t["credit"] for t in txs)
    assert tot_dr == 5000.0, f"Expected 5000.0 debits, got {tot_dr}"
    assert tot_cr == 13286.54, f"Expected 13286.54 credits, got {tot_cr}"
    assert txs[-1]["balance"] == 9771.85, "Ending balance mismatch"
    print("[PASS] Indian Bank Statement parsed with 100% precision!")

def test_csv_parser():
    csv_path = os.path.join(os.path.dirname(__file__), "sample_statement.csv")
    with open(csv_path, "rb") as f:
        data = f.read()
    res = parse_csv(data)
    hdr = res["header"]
    txs = res["transactions"]

    print("\n--- TEST: CSV Bank Statement ---")
    print(f"Holder       : {hdr.get('account_holder')}")
    print(f"Account No   : {hdr.get('account_number')}")
    print(f"Period       : {hdr.get('statement_from')} to {hdr.get('statement_to')}")
    print(f"Closing Bal  : {hdr.get('current_balance')}")
    print(f"Transactions : {len(txs)}")

    assert hdr.get("account_holder") == "RAJESH SHARMA"
    assert hdr.get("account_number") == "501004928172"
    assert hdr.get("current_balance") == 93341.0
    assert len(txs) == 13
    print("[PASS] CSV Bank Statement parsed perfectly!")

def test_excel_parser():
    # Generate in-memory Excel file to test xlsx parsing
    csv_path = os.path.join(os.path.dirname(__file__), "sample_statement.csv")
    df = pd.read_csv(csv_path, skiprows=5)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    buf.seek(0)

    res = parse_excel(buf.getvalue())
    txs = res["transactions"]
    print("\n--- TEST: Excel (.xlsx) Statement ---")
    print(f"Transactions : {len(txs)}")
    assert len(txs) == 13, f"Expected 13 transactions, got {len(txs)}"
    assert res["header"]["current_balance"] == 93341.0, "Closing balance mismatch"
    print("[PASS] Excel (.xlsx) parsed perfectly!")

def test_user_statement_indian_bank_pdf():
    pdf_path = r"C:\Users\haris\Downloads\AccountStatement (4).pdf"
    if not os.path.exists(pdf_path):
        return
    print("\n--- TEST: Real User PDF: Indian Bank Statement ---")
    with open(pdf_path, "rb") as f:
        res = parse_pdf(f.read())
    hdr = res["header"]
    txs = res["transactions"]
    print(f"Holder       : {hdr.get('account_holder')}")
    print(f"Bank         : {hdr.get('bank_name')}")
    print(f"Opening Bal  : {hdr.get('opening_balance')}")
    print(f"Current Bal  : {hdr.get('current_balance')}")
    print(f"Transactions : {len(txs)}")

    # Verify Row 6 (ATM debit) has debit = 5000.0, balance = 748.01
    atm_tx = next((t for t in txs if t["date"] == "2026-03-22"), None)
    assert atm_tx is not None, "2026-03-22 transaction not found"
    assert atm_tx["debit"] == 5000.0, f"Expected debit 5000.0, got {atm_tx['debit']}"
    assert atm_tx["balance"] == 748.01, f"Expected balance 748.01, got {atm_tx['balance']}"
    assert atm_tx["type"] == "debit", f"Expected type debit, got {atm_tx['type']}"

    total_debit = sum(t["debit"] for t in txs)
    total_credit = sum(t["credit"] for t in txs)
    assert total_debit == 5000.0, f"Expected total debit 5000.0, got {total_debit}"
    assert total_credit == 13286.54, f"Expected total credit 13286.54, got {total_credit}"
    assert hdr.get("current_balance") == 9771.85, f"Expected 9771.85, got {hdr.get('current_balance')}"
    print("[PASS] Real User Indian Bank PDF parsed with 100% debit/credit accuracy!")

def test_user_statement_sbi_password():
    pdf_path = r"C:\Users\haris\Downloads\AccountStatement_23102026_193817.pdf"
    if not os.path.exists(pdf_path):
        return
    from parsers.pdf_parser import PasswordRequiredError, InvalidPasswordError
    print("\n--- TEST: Real User PDF: SBI Encrypted Statement ---")
    with open(pdf_path, "rb") as f:
        content = f.read()

    # 1. No password -> PasswordRequiredError
    try:
        parse_pdf(content)
        assert False, "Should have raised PasswordRequiredError"
    except PasswordRequiredError:
        print("[PASS] Correctly detected password protection and requested password!")

    # 2. Wrong password -> InvalidPasswordError
    try:
        parse_pdf(content, password="wrongpassword")
        assert False, "Should have raised InvalidPasswordError"
    except InvalidPasswordError:
        print("[PASS] Correctly rejected invalid password!")

def test_salutation_name_extraction():
    from parsers.pdf_parser import _parse_page_header
    print("\n--- TEST: Salutation Name Detection (Mr., Mrs., Shri, etc.) ---")
    
    # Test case 1: Mr. HARISH BALAJI S with trailing spaces & address
    text1 = """
    STATE BANK OF INDIA
    Branch: GUINDY
    Mr. HARISH BALAJI S      
    4/1183 KEEL STREET
    Account Number: 39182910482
    """
    hdr1 = _parse_page_header(text1)
    print(f"Sample 1 Holder: {hdr1.get('account_holder')}")
    assert hdr1.get("account_holder") == "Mr. HARISH BALAJI S", f"Got: {hdr1.get('account_holder')}"

    # Test case 2: Mrs. PRIYA SHARMA
    text2 = """
    HDFC BANK
    Mrs. PRIYA SHARMA
    Address: 123 MG ROAD
    Account Number: 501004928172
    """
    hdr2 = _parse_page_header(text2)
    print(f"Sample 2 Holder: {hdr2.get('account_holder')}")
    assert hdr2.get("account_holder") == "Mrs. PRIYA SHARMA", f"Got: {hdr2.get('account_holder')}"

    # Test case 3: Shri. RAMESH CHANDRA
    text3 = """
    PUNJAB NATIONAL BANK
    Shri. RAMESH CHANDRA
    A/C No: 1234567890123
    """
    hdr3 = _parse_page_header(text3)
    print(f"Sample 3 Holder: {hdr3.get('account_holder')}")
    assert hdr3.get("account_holder") == "Shri. RAMESH CHANDRA", f"Got: {hdr3.get('account_holder')}"

    print("[PASS] Salutation-based account holder names extracted with 100% precision!")

if __name__ == "__main__":
    print("=" * 60)
    print("  RUNNING OFFLINE BANK STATEMENT TESTS")
    print("=" * 60)
    test_hdfc_pdf()
    test_indian_bank_ocr()
    test_csv_parser()
    test_excel_parser()
    test_user_statement_indian_bank_pdf()
    test_user_statement_sbi_password()
    test_salutation_name_extraction()
    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED WITH 100% ACCURACY!")
    print("=" * 60)
