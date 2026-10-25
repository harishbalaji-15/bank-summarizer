import React, { useState, useMemo } from 'react';
import { Landmark, Shield, RefreshCw } from 'lucide-react';
import FileUpload from './components/FileUpload';
import StatementHeader from './components/StatementHeader';
import SummaryCards from './components/SummaryCards';
import Charts from './components/Charts';
import TransactionFilters from './components/TransactionFilters';
import TransactionTable from './components/TransactionTable';

export default function App() {
  const [statementData, setStatementData] = useState(null);
  const [filename, setFilename] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters State
  const initialFilters = {
    search: '',
    type: 'all',
    category: 'all',
    startDate: '',
    endDate: '',
    minAmount: '',
    maxAmount: '',
    groupBy: 'none',
  };
  const [filters, setFilters] = useState(initialFilters);

  const handleUploadSuccess = (data, uploadedFilename) => {
    setStatementData(data);
    setFilename(uploadedFilename);
    setFilters(initialFilters);
  };

  const handleReset = () => {
    setStatementData(null);
    setFilename('');
    setError(null);
  };

  // Derive categories list from transactions
  const categories = useMemo(() => {
    if (!statementData?.transactions) return [];
    const set = new Set();
    statementData.transactions.forEach((tx) => {
      if (tx.category) set.add(tx.category.toLowerCase());
    });
    return Array.from(set).sort();
  }, [statementData]);

  // Filtered transactions
  const filteredTransactions = useMemo(() => {
    if (!statementData?.transactions) return [];

    return statementData.transactions.filter((tx) => {
      // Type filter
      if (filters.type !== 'all' && tx.type !== filters.type) {
        return false;
      }

      // Category filter
      if (filters.category !== 'all' && tx.category?.toLowerCase() !== filters.category) {
        return false;
      }

      // Search keyword filter
      if (filters.search) {
        const query = filters.search.toLowerCase();
        const matchesDesc = (tx.description || '').toLowerCase().includes(query);
        const matchesCat = (tx.category || '').toLowerCase().includes(query);
        if (!matchesDesc && !matchesCat) return false;
      }

      // Date range filter
      if (filters.startDate && tx.date < filters.startDate) {
        return false;
      }
      if (filters.endDate && tx.date > filters.endDate) {
        return false;
      }

      // Amount filter
      const txAmount = tx.type === 'debit' ? tx.debit : tx.credit;
      if (filters.minAmount !== '' && txAmount < Number(filters.minAmount)) {
        return false;
      }
      if (filters.maxAmount !== '' && txAmount > Number(filters.maxAmount)) {
        return false;
      }

      return true;
    });
  }, [statementData, filters]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-600 text-white flex items-center justify-center shadow-sm">
              <Landmark className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 tracking-tight leading-tight">
                Offline Bank Statement Summarizer
              </h1>
              <p className="text-[11px] text-slate-500 font-medium hidden sm:block">
                Secure local parser • PDF, CSV, Excel
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <Shield className="w-3.5 h-3.5 text-emerald-600" />
              <span>100% Offline</span>
            </span>

            {statementData && (
              <button
                onClick={handleReset}
                className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 flex items-center gap-1.5 transition-colors shadow-2xs"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">New Statement</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!statementData ? (
          <FileUpload
            onUploadSuccess={handleUploadSuccess}
            loading={loading}
            setLoading={setLoading}
            error={error}
            setError={setError}
          />
        ) : (
          <div>
            {/* Extracted Details Header */}
            <StatementHeader
              header={statementData.header}
              filename={filename}
              onReset={handleReset}
            />

            {/* Quick Summary Numbers */}
            <SummaryCards summary={statementData.summary} />

            {/* Visual Charts */}
            <Charts summary={statementData.summary} />

            {/* Detailed Transaction Section with Filters & Grouping */}
            <div className="mt-8">
              <TransactionFilters
                filters={filters}
                setFilters={setFilters}
                categories={categories}
                onReset={() => setFilters(initialFilters)}
              />

              <TransactionTable
                transactions={filteredTransactions}
                groupBy={filters.groupBy}
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Offline Bank Statement Summarizer • Data is processed on-device and never stored
      </footer>
    </div>
  );
}
