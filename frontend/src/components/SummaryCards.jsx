import React from 'react';
import { ArrowDownLeft, ArrowUpRight, Scale, Receipt, Wallet } from 'lucide-react';
import { formatInr } from '../utils/formatters';

export default function SummaryCards({ summary }) {
  const {
    total_debit = 0,
    total_credit = 0,
    net = 0,
    total_transactions = 0,
    current_balance = null,
  } = summary || {};

  const cards = [
    {
      title: 'Current / Closing Balance',
      amount: current_balance,
      formatted: current_balance !== null && current_balance !== undefined ? formatInr(current_balance) : '—',
      icon: Wallet,
      color: 'text-sky-600',
      bgColor: 'bg-sky-50',
      borderColor: 'border-sky-200/80',
      badge: 'Account Balance',
    },
    {
      title: 'Total Received (Credit)',
      amount: total_credit,
      formatted: formatInr(total_credit),
      icon: ArrowDownLeft,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200/80',
      badge: 'Money In',
    },
    {
      title: 'Total Spent (Debit)',
      amount: total_debit,
      formatted: formatInr(total_debit),
      icon: ArrowUpRight,
      color: 'text-rose-600',
      bgColor: 'bg-rose-50',
      borderColor: 'border-rose-200/80',
      badge: 'Money Out',
    },
    {
      title: 'Net Cash Flow',
      amount: net,
      formatted: `${net > 0 ? '+' : ''}${formatInr(net)}`,
      icon: Scale,
      color: net >= 0 ? 'text-teal-600' : 'text-amber-600',
      bgColor: net >= 0 ? 'bg-teal-50' : 'bg-amber-50',
      borderColor: net >= 0 ? 'border-teal-200/80' : 'border-amber-200/80',
      badge: net >= 0 ? 'Surplus' : 'Deficit',
    },
    {
      title: 'Total Transactions',
      amount: total_transactions,
      formatted: total_transactions.toString(),
      icon: Receipt,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200/80',
      badge: 'Records',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-5 rounded-2xl bg-white border ${card.borderColor} shadow-xs hover:shadow-md transition-all flex flex-col justify-between`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  {card.title}
                </span>
                <div className={`p-2 rounded-xl ${card.bgColor} ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className={`text-xl sm:text-2xl font-black ${card.color} tracking-tight`}>
                {card.formatted}
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Status</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${card.bgColor} ${card.color}`}>
                {card.badge}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
