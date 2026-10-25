import React from 'react';
import { User, Calendar, CreditCard, Wallet, Landmark, Building2, ArrowRight } from 'lucide-react';
import { formatInr, formatDate } from '../utils/formatters';

export default function StatementHeader({ header, filename, onReset }) {
  const {
    account_holder,
    account_number,
    bank_name,
    ifsc,
    statement_from,
    statement_to,
    opening_balance,
    current_balance,
  } = header || {};

  return (
    <div className="bg-gradient-to-br from-slate-900 via-sky-950 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl mb-8 relative overflow-hidden border border-slate-800">
      {/* Decorative ambient glow */}
      <div className="absolute -right-10 -bottom-10 w-72 h-72 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -left-10 -top-10 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Bar: Bank Badge & Account Holder */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10 relative z-10">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center text-sky-300 font-bold shadow-inner border border-white/10 flex-shrink-0">
            {bank_name ? <Building2 className="w-7 h-7 text-sky-400" /> : <User className="w-7 h-7" />}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1">
              {bank_name && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-sky-500/20 text-sky-300 border border-sky-400/30">
                  <Landmark className="w-3 h-3" />
                  {bank_name}
                </span>
              )}
              {ifsc && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-mono font-medium bg-white/10 text-slate-300 border border-white/10">
                  IFSC: {ifsc}
                </span>
              )}
            </div>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              {account_holder || 'Account Holder'}
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="text-right hidden sm:block">
            <span className="text-[11px] text-slate-400 block font-medium">Source File</span>
            <span className="text-xs font-mono text-sky-200 max-w-[200px] truncate block" title={filename}>
              {filename}
            </span>
          </div>
          <button
            onClick={onReset}
            className="text-xs font-semibold px-4 py-2.5 bg-white/10 hover:bg-white/20 active:scale-95 text-white rounded-xl transition-all border border-white/10 shadow-sm cursor-pointer"
          >
            Upload Another
          </button>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-6 relative z-10">
        {/* Account Number */}
        <div className="p-4 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-sm">
          <div className="flex items-center gap-2.5 text-slate-400 text-xs mb-1 font-medium">
            <CreditCard className="w-4 h-4 text-sky-400" />
            <span>Account Number</span>
          </div>
          <div className="text-sm sm:text-base font-bold text-slate-100 font-mono tracking-wider">
            {account_number || 'Not Available'}
          </div>
        </div>

        {/* Statement Period */}
        <div className="p-4 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-sm">
          <div className="flex items-center gap-2.5 text-slate-400 text-xs mb-1 font-medium">
            <Calendar className="w-4 h-4 text-sky-400" />
            <span>Statement Period</span>
          </div>
          <div className="text-xs sm:text-sm font-semibold text-slate-100">
            {statement_from ? (
              <span className="inline-flex items-center gap-1.5 flex-wrap">
                <span>{formatDate(statement_from)}</span>
                <ArrowRight className="w-3 h-3 text-slate-400 inline" />
                <span>{formatDate(statement_to)}</span>
              </span>
            ) : (
              'Full Records'
            )}
          </div>
        </div>

        {/* Opening Balance */}
        <div className="p-4 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-sm">
          <div className="flex items-center gap-2.5 text-slate-400 text-xs mb-1 font-medium">
            <Wallet className="w-4 h-4 text-slate-400" />
            <span>Opening Balance</span>
          </div>
          <div className="text-base sm:text-lg font-bold text-slate-200">
            {opening_balance !== null && opening_balance !== undefined
              ? formatInr(opening_balance)
              : '—'}
          </div>
        </div>

        {/* Current / Closing Balance (Highlighted) */}
        <div className="p-4 rounded-2xl bg-gradient-to-br from-sky-500/25 to-emerald-500/20 border border-sky-400/40 shadow-lg shadow-sky-500/5">
          <div className="flex items-center gap-2.5 text-sky-200 text-xs mb-1 font-semibold">
            <Wallet className="w-4 h-4 text-sky-300" />
            <span>Current / Closing Balance</span>
          </div>
          <div className="text-xl sm:text-2xl font-black text-white tracking-tight">
            {current_balance !== null && current_balance !== undefined
              ? formatInr(current_balance)
              : '—'}
          </div>
        </div>
      </div>
    </div>
  );
}
