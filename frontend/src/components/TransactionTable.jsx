import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Download, ChevronRight, ChevronDown, Columns, LayoutList } from 'lucide-react';
import { formatInr, formatDate, CATEGORY_COLORS } from '../utils/formatters';

export default function TransactionTable({ transactions = [], groupBy = 'none' }) {
  const [sortField, setSortField] = useState('date');
  const [sortDirection, setSortDirection] = useState('desc'); // 'asc' or 'desc'
  const [collapsedGroups, setCollapsedGroups] = useState({});
  const [viewMode, setViewMode] = useState('passbook'); // 'passbook' (separate Dr & Cr) or 'compact' (single amount)

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const toggleGroup = (key) => {
    setCollapsedGroups((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Sort logic
  const sortedTransactions = useMemo(() => {
    return [...transactions].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (sortField === 'amount') {
        valA = a.type === 'debit' ? a.debit : a.credit;
        valB = b.type === 'debit' ? b.debit : b.credit;
      }

      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      const res = valA > valB ? 1 : -1;
      return sortDirection === 'asc' ? res : -res;
    });
  }, [transactions, sortField, sortDirection]);

  // Grouping logic
  const groupedData = useMemo(() => {
    if (groupBy === 'none') {
      return [{ groupKey: 'All', items: sortedTransactions }];
    }

    const groups = {};
    sortedTransactions.forEach((tx) => {
      let key = 'Other';
      if (groupBy === 'category') {
        key = tx.category ? tx.category.charAt(0).toUpperCase() + tx.category.slice(1) : 'Other';
      } else if (groupBy === 'month') {
        key = tx.date ? tx.date.substring(0, 7) : 'Unknown';
      } else if (groupBy === 'day') {
        key = tx.date || 'Unknown';
      }

      if (!groups[key]) {
        groups[key] = {
          items: [],
          totalDebit: 0,
          totalCredit: 0,
        };
      }
      groups[key].items.push(tx);
      groups[key].totalDebit += tx.debit || 0;
      groups[key].totalCredit += tx.credit || 0;
    });

    return Object.entries(groups).map(([groupKey, data]) => ({
      groupKey,
      items: data.items,
      totalDebit: data.totalDebit,
      totalCredit: data.totalCredit,
    }));
  }, [sortedTransactions, groupBy]);

  // Total summary for current filtered view
  const totals = useMemo(() => {
    let deb = 0;
    let cred = 0;
    sortedTransactions.forEach((t) => {
      deb += t.debit || 0;
      cred += t.credit || 0;
    });
    return { debit: deb, credit: cred, net: cred - deb };
  }, [sortedTransactions]);

  // CSV Export
  const exportToCsv = () => {
    if (!sortedTransactions.length) return;
    const headers = ['Date', 'Description', 'Category', 'Type', 'Debit (Withdrawal)', 'Credit (Deposit)', 'Balance'];
    const rows = sortedTransactions.map((t) => [
      t.date,
      `"${(t.description || '').replace(/"/g, '""')}"`,
      t.category,
      t.type,
      t.debit || 0,
      t.credit || 0,
      t.balance !== null && t.balance !== undefined ? t.balance : '',
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'bank_statement_transactions.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />;
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="w-3.5 h-3.5 text-sky-600" />
    ) : (
      <ArrowDown className="w-3.5 h-3.5 text-sky-600" />
    );
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-12">
      {/* Table Header Bar */}
      <div className="p-5 border-b border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-900">Extracted Transactions</h3>
          <p className="text-xs text-slate-500">
            Showing {sortedTransactions.length} transaction{sortedTransactions.length !== 1 ? 's' : ''}
            {groupBy !== 'none' && ` across ${groupedData.length} ${groupBy} groups`}
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          {/* View mode toggle */}
          <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/80">
            <button
              onClick={() => setViewMode('passbook')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                viewMode === 'passbook'
                  ? 'bg-white text-slate-800 shadow-xs'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
              title="Passbook View (Separate Debit and Credit columns)"
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Passbook</span>
            </button>
            <button
              onClick={() => setViewMode('compact')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                viewMode === 'compact'
                  ? 'bg-white text-slate-800 shadow-xs'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
              title="Compact View (Single amount column)"
            >
              <LayoutList className="w-3.5 h-3.5" />
              <span>Compact</span>
            </button>
          </div>

          <button
            onClick={exportToCsv}
            disabled={!sortedTransactions.length}
            className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors disabled:opacity-50 cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export CSV</span>
          </button>
        </div>
      </div>

      {sortedTransactions.length === 0 ? (
        <div className="py-16 text-center text-slate-400 text-sm">
          No transactions match your current filters.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                <th
                  onClick={() => handleSort('date')}
                  className="py-3 px-4 cursor-pointer select-none group hover:bg-slate-100/80 transition-colors whitespace-nowrap"
                >
                  <div className="flex items-center gap-1.5">
                    Date <SortIcon field="date" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('description')}
                  className="py-3 px-4 cursor-pointer select-none group hover:bg-slate-100/80 transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    Narration / Description <SortIcon field="description" />
                  </div>
                </th>
                <th className="py-3 px-4 whitespace-nowrap">Category</th>

                {viewMode === 'passbook' ? (
                  <>
                    <th
                      onClick={() => handleSort('debit')}
                      className="py-3 px-4 text-right cursor-pointer select-none group hover:bg-slate-100/80 transition-colors whitespace-nowrap text-rose-600"
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        Withdrawal (Dr) <SortIcon field="debit" />
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('credit')}
                      className="py-3 px-4 text-right cursor-pointer select-none group hover:bg-slate-100/80 transition-colors whitespace-nowrap text-emerald-600"
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        Deposit (Cr) <SortIcon field="credit" />
                      </div>
                    </th>
                  </>
                ) : (
                  <th
                    onClick={() => handleSort('amount')}
                    className="py-3 px-4 text-right cursor-pointer select-none group hover:bg-slate-100/80 transition-colors whitespace-nowrap"
                  >
                    <div className="flex items-center justify-end gap-1.5">
                      Debit / Credit <SortIcon field="amount" />
                    </div>
                  </th>
                )}

                <th
                  onClick={() => handleSort('balance')}
                  className="py-3 px-4 text-right cursor-pointer select-none group hover:bg-slate-100/80 transition-colors whitespace-nowrap"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    Balance <SortIcon field="balance" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {groupedData.map((group) => {
                const isCollapsed = collapsedGroups[group.groupKey];
                return (
                  <React.Fragment key={group.groupKey}>
                    {groupBy !== 'none' && (
                      <tr
                        onClick={() => toggleGroup(group.groupKey)}
                        className="bg-slate-100/70 border-b border-slate-200 font-semibold cursor-pointer hover:bg-slate-100 transition-colors select-none"
                      >
                        <td colSpan={viewMode === 'passbook' ? 6 : 5} className="py-2.5 px-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-slate-800">
                              {isCollapsed ? (
                                <ChevronRight className="w-4 h-4 text-slate-500" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-slate-500" />
                              )}
                              <span>{group.groupKey}</span>
                              <span className="text-slate-400 font-normal">({group.items.length})</span>
                            </div>
                            <div className="flex items-center gap-4 text-right text-[11px]">
                              {group.totalDebit > 0 && (
                                <span className="text-rose-600 font-bold">
                                  Debits: -{formatInr(group.totalDebit)}
                                </span>
                              )}
                              {group.totalCredit > 0 && (
                                <span className="text-emerald-600 font-bold">
                                  Credits: +{formatInr(group.totalCredit)}
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}

                    {!isCollapsed &&
                      group.items.map((tx, idx) => {
                        const isDebit = tx.type === 'debit';
                        const catColor = CATEGORY_COLORS[tx.category?.toLowerCase()] || CATEGORY_COLORS.other;

                        return (
                          <tr
                            key={idx}
                            className="border-b border-slate-100 hover:bg-slate-50/70 transition-colors"
                          >
                            {/* Date */}
                            <td className="py-3 px-4 whitespace-nowrap font-medium text-slate-600">
                              {formatDate(tx.date)}
                            </td>

                            {/* Narration */}
                            <td className="py-3 px-4 max-w-xs md:max-w-md lg:max-w-lg font-normal text-slate-800">
                              <div className="break-words line-clamp-2" title={tx.description}>
                                {tx.description}
                              </div>
                            </td>

                            {/* Category Badge */}
                            <td className="py-3 px-4 whitespace-nowrap">
                              <span
                                className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold"
                                style={{
                                  backgroundColor: `${catColor}15`,
                                  color: catColor,
                                }}
                              >
                                {tx.category ? tx.category.charAt(0).toUpperCase() + tx.category.slice(1) : 'Other'}
                              </span>
                            </td>

                            {/* Passbook View (Separate Debit and Credit columns) */}
                            {viewMode === 'passbook' ? (
                              <>
                                <td className="py-3 px-4 text-right whitespace-nowrap font-mono font-bold text-rose-600">
                                  {tx.debit > 0 ? formatInr(tx.debit) : '—'}
                                </td>
                                <td className="py-3 px-4 text-right whitespace-nowrap font-mono font-bold text-emerald-600">
                                  {tx.credit > 0 ? formatInr(tx.credit) : '—'}
                                </td>
                              </>
                            ) : (
                              /* Compact View (Single column) */
                              <td className="py-3 px-4 text-right whitespace-nowrap font-mono font-bold">
                                {isDebit ? (
                                  <span className="text-rose-600">- {formatInr(tx.debit)}</span>
                                ) : (
                                  <span className="text-emerald-600">+ {formatInr(tx.credit)}</span>
                                )}
                              </td>
                            )}

                            {/* Running Balance */}
                            <td className="py-3 px-4 text-right whitespace-nowrap text-slate-700 font-mono font-medium">
                              {tx.balance !== null && tx.balance !== undefined ? formatInr(tx.balance) : '—'}
                            </td>
                          </tr>
                        );
                      })}
                  </React.Fragment>
                );
              })}
            </tbody>
            {/* Table Footer with Totals */}
            <tfoot>
              <tr className="bg-slate-50 border-t-2 border-slate-200 text-slate-800 font-bold text-xs">
                <td colSpan={3} className="py-3.5 px-4">
                  <span>Filtered Totals ({sortedTransactions.length} records)</span>
                </td>
                {viewMode === 'passbook' ? (
                  <>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap font-mono text-rose-600 font-extrabold">
                      {totals.debit > 0 ? formatInr(totals.debit) : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap font-mono text-emerald-600 font-extrabold">
                      {totals.credit > 0 ? formatInr(totals.credit) : '—'}
                    </td>
                  </>
                ) : (
                  <td className="py-3.5 px-4 text-right whitespace-nowrap font-mono">
                    <span className="text-rose-600 mr-2">Dr: {formatInr(totals.debit)}</span>
                    <span className="text-emerald-600">Cr: {formatInr(totals.credit)}</span>
                  </td>
                )}
                <td className="py-3.5 px-4 text-right whitespace-nowrap text-slate-500 font-normal">
                  —
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
