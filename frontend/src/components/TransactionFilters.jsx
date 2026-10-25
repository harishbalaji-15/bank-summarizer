import React from 'react';
import { Search, Filter, Layers, X, Calendar, DollarSign } from 'lucide-react';

export default function TransactionFilters({
  filters,
  setFilters,
  categories,
  onReset,
}) {
  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const hasActiveFilters =
    filters.search ||
    filters.type !== 'all' ||
    filters.category !== 'all' ||
    filters.startDate ||
    filters.endDate ||
    filters.minAmount ||
    filters.maxAmount ||
    filters.groupBy !== 'none';

  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm mb-6">
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 mb-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search transactions by narration, description or keyword..."
            value={filters.search}
            onChange={(e) => updateFilter('search', e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all"
          />
          {filters.search && (
            <button
              onClick={() => updateFilter('search', '')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Group By selector */}
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-sky-600 flex-shrink-0" />
          <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">Group By:</span>
          <select
            value={filters.groupBy}
            onChange={(e) => updateFilter('groupBy', e.target.value)}
            className="text-xs font-medium py-2 px-3 rounded-xl border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="none">No Grouping (Flat List)</option>
            <option value="category">Category</option>
            <option value="month">Month</option>
            <option value="day">Day / Date</option>
          </select>
        </div>
      </div>

      {/* Filter Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-3 border-t border-slate-100">
        {/* Type Filter */}
        <div>
          <label className="text-[11px] font-semibold text-slate-500 block mb-1">Type</label>
          <select
            value={filters.type}
            onChange={(e) => updateFilter('type', e.target.value)}
            className="w-full text-xs py-1.5 px-2.5 rounded-lg border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="all">All Types</option>
            <option value="debit">Debit (Spent)</option>
            <option value="credit">Credit (Received)</option>
          </select>
        </div>

        {/* Category Filter */}
        <div>
          <label className="text-[11px] font-semibold text-slate-500 block mb-1">Category</label>
          <select
            value={filters.category}
            onChange={(e) => updateFilter('category', e.target.value)}
            className="w-full text-xs py-1.5 px-2.5 rounded-lg border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="all">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Start Date */}
        <div>
          <label className="text-[11px] font-semibold text-slate-500 block mb-1">From Date</label>
          <input
            type="date"
            value={filters.startDate}
            onChange={(e) => updateFilter('startDate', e.target.value)}
            className="w-full text-xs py-1.5 px-2 rounded-lg border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        {/* End Date */}
        <div>
          <label className="text-[11px] font-semibold text-slate-500 block mb-1">To Date</label>
          <input
            type="date"
            value={filters.endDate}
            onChange={(e) => updateFilter('endDate', e.target.value)}
            className="w-full text-xs py-1.5 px-2 rounded-lg border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        {/* Min Amount */}
        <div>
          <label className="text-[11px] font-semibold text-slate-500 block mb-1">Min ₹</label>
          <input
            type="number"
            placeholder="Min amount"
            value={filters.minAmount}
            onChange={(e) => updateFilter('minAmount', e.target.value)}
            className="w-full text-xs py-1.5 px-2 rounded-lg border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        {/* Max Amount */}
        <div>
          <label className="text-[11px] font-semibold text-slate-500 block mb-1">Max ₹</label>
          <input
            type="number"
            placeholder="Max amount"
            value={filters.maxAmount}
            onChange={(e) => updateFilter('maxAmount', e.target.value)}
            className="w-full text-xs py-1.5 px-2 rounded-lg border border-slate-200 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>
      </div>

      {hasActiveFilters && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs text-sky-700 font-medium">Filters active</span>
          <button
            onClick={onReset}
            className="text-xs font-semibold text-rose-600 hover:text-rose-700 flex items-center gap-1"
          >
            <X className="w-3.5 h-3.5" /> Clear All Filters
          </button>
        </div>
      )}
    </div>
  );
}
