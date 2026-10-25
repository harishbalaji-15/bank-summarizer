import re

full_ocr = '''
ACCOUNT STATEMENT
For period: 01 Feb 2026 - 06 May 2026
ACCOUNT DETAILS
Account Holder Name USHA KUMAR
Account Type Savings
Account Number 6032183663
Customer's Address 4/1183 KEEL STREET
ARASANKUPPAM
MELERI POST
ARAKKONAM TK
VELLORE DT
Branch Name MINNAL
IFSC IDIB000M038
Account Currency INR
ACCOUNT SUMMARY
Opening Balance INR 1,485.31
Total Credits + INR 13,286.54
Total Debits - INR 5,000.00
Ending Balance INR 9,771.85
ACCOUNT ACTIVITY
Date Transaction Details Debits Credits Balance
03 Feb 2026 TRANSFER FROM
94966000128
NEFT/HDFC/HDFCN52026
020357042216/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 928.80 INR 2,414.11
13 Feb 2026 TRANSFER FROM
97166000126
NEFT/HDFC/HDFCN52026
021383595525/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 861.16 INR 3,275.27
23 Feb 2026 TRANSFER FROM
97168000124
NEFT/HDFC/HDFCN52026
022398734455/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 805.25 INR 4,080.52
03 Mar 2026 TRANSFER FROM
97168000124
NEFT/HDFC/HDFCN52026
030317664624/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 765.75 INR 4,846.27
13 Mar 2026 TRANSFER FROM
97165000127
NEFT/HDFC/HDFCN52026
031343844797/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 901.74 INR 5,748.01
22 Mar 2026 TRAN DATE -(MMDD) 0322
TRAN TIME -(HHMMSS)
081153/SELF
AMARTHAVALLI COMP
GOVE SANKARAPURAM
IN/ATM WDL SEQ NO
608108012050 ATM ID
MCRM4565 /BRANCH :
MINNAL
INR 5,000.00 - INR 748.01
23 Mar 2026 TRANSFER FROM
97161000121
NEFT/HDFC/HDFCN52026
032359310166/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 1,697.51 INR 2,445.52
31 Mar 2026 CREDIT INTEREST - INR 22.00 INR 2,467.52
03 Apr 2026 TRANSFER FROM
94958000127
NEFT/HDFC/HDFCN52026
040385456968/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 1,416.95 INR 3,884.47
13 Apr 2026 TRANSFER FROM
97168000124
NEFT/HDFC/HDFCN52026
041307493906/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 2,475.63 INR 6,360.10
23 Apr 2026 TRANSFER FROM
94964000120
NEFT/HDFC/HDFCN52026
042327232736/HATSUN
AGR//BRANCH : MUMBAI
FORT
 - INR 2,476.51 INR 8,836.61
03 May 2026 TRANSFER FROM
94963000121
NEFT/HDFC/HDFCN52026
050346810185/HATSU
 - INR 935.24 INR 9,771.85
N AGR//BRANCH :
MUMBAI FORT
Ending Balance INR 9,771.85
Total INR 5,000.00 INR 13,286.54
'''

DATE_PAT = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'

header = {}
name_m = re.search(r'Account\s*Holder(?:\s*Name)?[\s:]+([A-Za-z\s\.]+?)(?=\s*(?:Account\s*Type|Account\s*No|Account\s*Number|Customer|Branch|Address|\n|$))', full_ocr, re.I)
header['account_holder'] = name_m.group(1).strip() if name_m else None

acct_m = re.search(r'Account\s*Number[\s:]+(\d{8,25})', full_ocr, re.I)
header['account_number'] = acct_m.group(1).strip() if acct_m else None

period_m = re.search(r'(?:For\s*period|Statement\s*period|Period)[\s:]*(' + DATE_PAT + r')\s*[-–to]+\s*(' + DATE_PAT + r')', full_ocr, re.I)
if period_m:
    header['statement_from'] = period_m.group(1).strip()
    header['statement_to'] = period_m.group(3).strip()

end_bal = re.search(r'(?:ending|closing|available|current|ledger|clear|effective\s+available)\s*bal(?:ance)?[\s:₹Rs.INR]*([0-9,]+\.?\d{0,2})', full_ocr, re.I)
open_bal = re.search(r'opening\s*bal(?:ance)?[\s:₹Rs.INR]*([0-9,]+\.?\d{0,2})', full_ocr, re.I)
header['current_balance'] = float(end_bal.group(1).replace(',', '')) if end_bal else None
opening_balance = float(open_bal.group(1).replace(',', '')) if open_bal else None

lines = full_ocr.split('\n')
blocks = []
curr = []
in_act = False
for line in lines:
    if 'ACCOUNT ACTIVITY' in line or 'Transaction Details' in line:
        in_act = True
        continue
    if not in_act:
        continue
    if 'Ending Balance' in line or ('Total' in line and 'INR' in line):
        if curr:
            blocks.append(curr)
            curr = []
        break
    if re.match(r'^\s*' + DATE_PAT, line, re.I):
        if curr:
            blocks.append(curr)
        curr = [line]
    elif curr:
        curr.append(line)
if curr:
    blocks.append(curr)

transactions = []
prev_bal = opening_balance

for b in blocks:
    dm = re.match(r'^\s*' + DATE_PAT, b[0], re.I)
    date_str = dm.group(1) if dm else ''

    amt_line = ''
    narration_lines = []
    for l in b:
        cleaned_l = l.strip()
        if re.search(r'(?:INR|Rs\.?|₹)?\s*[0-9,]+\.\d{2}', cleaned_l):
            amt_line = cleaned_l
            without_date = re.sub(r'^\s*' + DATE_PAT, '', cleaned_l, flags=re.I).strip()
            m_before = re.split(r'(?:(?:\s+-\s+)?(?:INR|Rs\.?|₹)?\s*[0-9,]+\.\d{2}|-\s+(?:INR|Rs\.?|₹)?)', without_date)
            if m_before and m_before[0].strip():
                narration_lines.append(m_before[0].strip())
        else:
            cleaned_narr = re.sub(r'^\s*' + DATE_PAT, '', cleaned_l, flags=re.I).strip()
            if cleaned_narr:
                narration_lines.append(cleaned_narr)

    narration = ' '.join(narration_lines)
    debit = 0.0
    credit = 0.0
    balance = None

    m_credit = re.search(r'-\s*(?:INR|Rs\.?|₹)?\s*([0-9,]+\.\d{2})\s*(?:INR|Rs\.?|₹)?\s*([0-9,]+\.\d{2})', amt_line)
    m_debit = re.search(r'(?:INR|Rs\.?|₹)?\s*([0-9,]+\.\d{2})\s*-\s*(?:INR|Rs\.?|₹)?\s*([0-9,]+\.\d{2})', amt_line)

    if m_credit:
        credit = float(m_credit.group(1).replace(',', ''))
        balance = float(m_credit.group(2).replace(',', ''))
    elif m_debit:
        debit = float(m_debit.group(1).replace(',', ''))
        balance = float(m_debit.group(2).replace(',', ''))
    else:
        nums = re.findall(r'([0-9,]+\.\d{2})', amt_line)
        nums = [float(n.replace(',', '')) for n in nums]
        if len(nums) >= 2:
            amt = nums[0]
            balance = nums[1]
            if prev_bal is not None:
                diff = round(balance - prev_bal, 2)
                if diff > 0:
                    credit = diff
                else:
                    debit = abs(diff)

    # Mathematical verification with running balance
    if balance is not None and prev_bal is not None:
        expected_diff = round(balance - prev_bal, 2)
        if expected_diff > 0:
            credit = expected_diff
            debit = 0.0
        elif expected_diff < 0:
            debit = abs(expected_diff)
            credit = 0.0

    if balance is not None:
        prev_bal = balance

    transactions.append({
        'date': date_str,
        'description': narration,
        'debit': debit,
        'credit': credit,
        'balance': balance,
        'type': 'credit' if credit > 0 else 'debit'
    })

if __name__ == "__main__":
    tot_debit = sum(t['debit'] for t in transactions)
    tot_credit = sum(t['credit'] for t in transactions)

    print("Header:", header)
    print("Total transactions:", len(transactions))
    print("Calculated Debits :", tot_debit)
    print("Calculated Credits:", tot_credit)
    print("Ending Balance    :", transactions[-1]['balance'] if transactions else None)
    for idx, t in enumerate(transactions):
        print(f"[{idx+1:02d}] {t['date']} | {t['type'].upper():<6} | Dr: {t['debit']:>8.2f} | Cr: {t['credit']:>8.2f} | Bal: {t['balance']:>8.2f} | {t['description'][:35]}")
