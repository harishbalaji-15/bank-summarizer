// Indian Rupee & Number Formatting
export function formatInr(amount, compact = false) {
  if (amount === null || amount === undefined || isNaN(amount)) return '₹0.00';
  const num = Math.abs(Number(amount));
  const sign = Number(amount) < 0 ? '-' : '';

  if (compact) {
    if (num >= 1e7) return `${sign}₹${(num / 1e7).toFixed(2)} Cr`;
    if (num >= 1e5) return `${sign}₹${(num / 1e5).toFixed(2)} L`;
    if (num >= 1e3) return `${sign}₹${(num / 1e3).toFixed(1)} K`;
  }

  // en-IN currency formatting
  return `${sign}₹` + num.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

// Friendly date formatting (e.g., 2024-03-15 -> 15 Mar 2024)
export function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  } catch {
    return dateStr;
  }
}

export function formatMonth(ym) {
  if (!ym) return '—';
  try {
    const [year, month] = ym.split('-');
    const d = new Date(year, parseInt(month, 10) - 1, 1);
    return d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
  } catch {
    return ym;
  }
}

export const CATEGORY_COLORS = {
  food: '#f97316',          // Orange
  shopping: '#8b5cf6',      // Purple
  utilities: '#0284c7',     // Sky blue
  transport: '#06b6d4',     // Cyan
  health: '#10b981',        // Emerald
  entertainment: '#ec4899', // Pink
  finance: '#3b82f6',       // Blue
  atm: '#78716c',           // Stone
  salary: '#22c55e',        // Green
  upi: '#6366f1',           // Indigo
  other: '#94a3b8',         // Slate
};
