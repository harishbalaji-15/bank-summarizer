# Offline Bank Statement Summarizer

A **100% offline** bank statement analyzer with a local Python FastAPI backend and a responsive React (Vite + Tailwind CSS) frontend designed for both desktop and mobile browsers.

---

## ⚡ Highlights

- **🔒 100% Offline & Private:** Statements are processed locally on your machine. No cloud uploads, no API keys, no tracking.
- **📄 Supported Formats:** PDF, CSV, Excel (`.xlsx`, `.xls`).
- **👤 Extracted Account Details:**
  - Account Holder Name
  - Account Number
  - Statement Period (From & To dates)
  - Current / Closing Balance
- **📊 Summary & Visual Analytics:**
  - Total Debits (Spent) & Credits (Deposits)
  - Net Cash Flow & Total Transaction Count
  - Interactive **Pie Chart** (Spending distribution across categories)
  - Monthly **Bar Chart** (Inflow vs Outflow comparison)
- **🏷️ Smart Auto-Categorization:**
  - Food & Dining (Swiggy, Zomato, cafes)
  - Shopping (Amazon, Flipkart, retail)
  - Utilities & Bills (Electricity, mobile, internet)
  - Transport (Uber, Ola, fuel/petrol)
  - Healthcare (Pharmacies, clinics)
  - Entertainment (Netflix, movies)
  - Investments & Banking (SIP, mutual funds, loans)
  - Salary, UPI, Cash ATM withdrawals
- **🔍 Advanced Filtering & Grouping:**
  - Filter by transaction type (Debit / Credit)
  - Filter by category
  - Filter by custom date range
  - Filter by Min / Max ₹ amount
  - Full-text search across narrations
  - **Group transactions by:** Category, Month, or Day (with sub-totals!)
  - Sort by Date, Narration, Amount
  - **Export filtered records to CSV**

---

## 🚀 Quick Launch (One-Click)

Just double-click:
```text
start_app.bat
```
This automatically launches:
1. Python FastAPI Backend on `http://localhost:8000`
2. React + Vite Frontend on `http://localhost:5173`
3. Opens your default browser automatically!

---

## 🛠️ Manual Launch

### Step 1: Start Backend
```powershell
cd backend
python main.py
```
> Running on **http://localhost:8000** (Interactive API docs at http://localhost:8000/docs)

### Step 2: Start Frontend
```powershell
cd frontend
npm run dev
```
> Open browser at **http://localhost:5173**

---

## 🧪 Testing with Sample Statement

A sample bank statement is included for instant testing:
`backend/sample_statement.csv`

To test directly from terminal:
```powershell
cd backend
python test_backend.py sample_statement.csv
```
Or simply drag & drop `sample_statement.csv` into the web app at `http://localhost:5173`!

---

## 📁 Project Structure

```
bank-summarizer/
├── start_app.bat             # 1-click launcher (Backend + Frontend + Browser)
├── start_backend.bat         # Launch backend only
├── start_frontend.bat        # Launch frontend only
│
├── backend/                  # Python FastAPI Backend
│   ├── main.py               # Server entry point & CORS
│   ├── requirements.txt      # Dependencies (fastapi, pdfplumber, pandas, etc.)
│   ├── create_sample_statement.py # Sample statement generator
│   ├── sample_statement.csv  # Ready-to-test bank statement
│   ├── test_backend.py       # Terminal smoke test script
│   ├── parsers/
│   │   ├── pdf_parser.py     # pdfplumber table & header extractor
│   │   └── csv_excel_parser.py # pandas CSV & Excel parser
│   └── routers/
│       └── parse.py          # /api/parse upload endpoint
│
└── frontend/                 # React + Vite + Tailwind CSS Frontend
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── App.jsx           # Main state, filtering & layout
        ├── main.jsx
        ├── index.css
        ├── utils/
        │   └── formatters.js # Indian Rupee (₹), date & category helpers
        └── components/
            ├── FileUpload.jsx         # Drag-and-drop file uploader
            ├── StatementHeader.jsx    # Extracted account details card
            ├── SummaryCards.jsx       # 4 key financial metrics
            ├── Charts.jsx             # Recharts Pie & Bar charts
            ├── TransactionFilters.jsx # Search, Type, Category, Date & Amount filters
            └── TransactionTable.jsx   # Detailed table, grouping & CSV export
```
