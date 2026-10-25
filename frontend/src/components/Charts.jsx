import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts';
import { CATEGORY_COLORS, formatInr, formatMonth } from '../utils/formatters';

export default function Charts({ summary }) {
  const { category_breakdown = {}, monthly_breakdown = {} } = summary || {};

  // Prepare Pie Chart data (only positive spend categories)
  const pieData = Object.entries(category_breakdown)
    .filter(([_, value]) => value > 0)
    .map(([category, value]) => ({
      name: category.charAt(0).toUpperCase() + category.slice(1),
      value: Math.round(value * 100) / 100,
      color: CATEGORY_COLORS[category.toLowerCase()] || CATEGORY_COLORS.other,
    }))
    .sort((a, b) => b.value - a.value);

  const totalSpent = pieData.reduce((acc, curr) => acc + curr.value, 0);

  // Prepare Monthly Bar Chart data
  const barData = Object.entries(monthly_breakdown).map(([month, stats]) => ({
    month: formatMonth(month),
    debit: stats.debit,
    credit: stats.credit,
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const percent = totalSpent > 0 ? ((data.value / totalSpent) * 100).toFixed(1) : 0;
      return (
        <div className="bg-slate-900 text-white p-3 rounded-xl shadow-lg text-xs">
          <p className="font-semibold">{data.name}</p>
          <p className="text-sky-300 font-bold">{formatInr(data.value)} ({percent}%)</p>
        </div>
      );
    }
    return null;
  };

  const BarTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 text-white p-3 rounded-xl shadow-lg text-xs space-y-1">
          <p className="font-semibold border-b border-slate-700 pb-1">{label}</p>
          {payload.map((entry, idx) => (
            <p key={idx} style={{ color: entry.color }} className="font-medium">
              {entry.name}: {formatInr(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      {/* Category Pie Chart */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
        <div className="mb-4">
          <h3 className="text-base font-bold text-slate-800">Spending by Category</h3>
          <p className="text-xs text-slate-500">Distribution of debits across auto-detected categories</p>
        </div>

        {pieData.length > 0 ? (
          <div className="flex-1 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="w-full md:w-1/2 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Top Categories legend list */}
            <div className="w-full md:w-1/2 space-y-2 max-h-60 overflow-y-auto pr-2">
              {pieData.map((item, idx) => {
                const percent = totalSpent > 0 ? ((item.value / totalSpent) * 100).toFixed(0) : 0;
                return (
                  <div key={idx} className="flex items-center justify-between text-xs py-1 border-b border-slate-100 last:border-0">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                      <span className="font-medium text-slate-700">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-semibold text-slate-900">{formatInr(item.value, true)}</span>
                      <span className="text-slate-400 ml-1.5 font-normal">({percent}%)</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm italic">
            No debit expenses found to categorize.
          </div>
        )}
      </div>

      {/* Monthly Bar Chart */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
        <div className="mb-4">
          <h3 className="text-base font-bold text-slate-800">Monthly Cash Inflow & Outflow</h3>
          <p className="text-xs text-slate-500">Compare monthly debits (spending) vs credits (deposits)</p>
        </div>

        {barData.length > 0 ? (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fontSize: 10, fill: '#64748b' }}
                  tickFormatter={(val) => formatInr(val, true)}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<BarTooltip />} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                <Bar dataKey="debit" name="Spent (Debit)" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="credit" name="Received (Credit)" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm italic">
            No monthly data to display.
          </div>
        )}
      </div>
    </div>
  );
}
