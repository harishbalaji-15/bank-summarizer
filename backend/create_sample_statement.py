"""
Generate realistic sample bank statements (CSV and borderless PDF) for instant testing.
Run: python create_sample_statement.py
"""
import csv
import os

sample_data = [
    ["Date", "Narration / Description", "Chq/Ref No", "Debit", "Credit", "Balance"],
    ["01/10/2024", "SALARY CREDIT - TECH CORP PVT LTD", "SAL20241001", "", "125000.00", "145000.00"],
    ["02/10/2024", "UPI-SWIGGY-swiggy@axis-ORDER123847", "UPI9823471", "540.00", "", "144460.00"],
    ["03/10/2024", "UPI-AMAZON PAY-amazon@apl-GROCERY", "UPI9823472", "2350.00", "", "142110.00"],
    ["05/10/2024", "NEFT TO LANDLORD RENT OCT", "NEFT491028", "28000.00", "", "114110.00"],
    ["07/10/2024", "UPI-UBER INDIA-uber@hdfc-RIDE", "UPI9823473", "420.00", "", "113690.00"],
    ["10/10/2024", "ELECTRICITY BILL TNEB ONLINE", "BILL89123", "1850.00", "", "111840.00"],
    ["12/10/2024", "ATM CASH WITHDRAWAL INDIRANAGAR", "ATM10293", "5000.00", "", "106840.00"],
    ["15/10/2024", "UPI-ZOMATO-zomato@icici-LUNCH", "UPI9823474", "380.00", "", "106460.00"],
    ["18/10/2024", "APOLLO PHARMACY HEALTHCARE", "POS91823", "1420.00", "", "105040.00"],
    ["20/10/2024", "SIP MUTUAL FUND HDFC EQUITY", "MF891234", "10000.00", "", "95040.00"],
    ["22/10/2024", "INTEREST CREDIT OCT 2024", "INT202410", "", "450.00", "95490.00"],
    ["25/10/2024", "NETFLIX SUBSCRIPTION ENTERTAINMENT", "SUB10293", "649.00", "", "94841.00"],
    ["28/10/2024", "UPI-SHELL PETROL PUMP FUEL", "UPI9823475", "1500.00", "", "93341.00"],
]

def create_sample_csv():
    output_path = os.path.join(os.path.dirname(__file__), "sample_statement.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Statement of Account: RAJESH SHARMA"])
        writer.writerow(["Account Number: 501004928172"])
        writer.writerow(["Period: 01/10/2024 to 28/10/2024"])
        writer.writerow(["Closing Balance: 93341.00"])
        writer.writerow([])
        writer.writerows(sample_data)
    print(f"Created sample CSV: {output_path}")
    return output_path

def create_sample_pdf():
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    output_path = os.path.join(os.path.dirname(__file__), "sample_statement.pdf")
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Bank header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "HDFC BANK LIMITED")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 75, "STATEMENT OF ACCOUNT")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 95, "Account Holder: RAJESH SHARMA")
    c.drawString(50, height - 110, "Account Number: 501004928172")
    c.drawString(50, height - 125, "Statement Period: 01/10/2024 to 28/10/2024")
    c.drawString(50, height - 140, "Available Balance: INR 93,341.00")

    # Table header line (borderless style with text spacing)
    y = height - 170
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "Txn Date")
    c.drawString(120, y, "Narration")
    c.drawString(350, y, "Debit (Dr)")
    c.drawString(430, y, "Credit (Cr)")
    c.drawString(510, y, "Closing Bal")

    c.setLineWidth(0.5)
    c.line(50, y - 5, 570, y - 5)
    y -= 20

    c.setFont("Helvetica", 8)
    for row in sample_data[1:]:
        date, desc, ref, debit, credit, bal = row
        c.drawString(50, y, date)
        # Truncate narration if too long
        narration = desc[:45]
        c.drawString(120, y, narration)
        if debit:
            c.drawString(350, y, debit)
        if credit:
            c.drawString(430, y, credit)
        c.drawString(510, y, bal)
        y -= 18

    c.save()
    print(f"Created sample PDF: {output_path}")
    return output_path

if __name__ == "__main__":
    create_sample_csv()
    create_sample_pdf()
