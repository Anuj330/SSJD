// Client-side CSV export. Excel opens .csv natively; the BOM keeps ₹/UTF-8 intact.

function escapeCell(v) {
  const s = v == null ? '' : String(v);
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/**
 * Download rows as a CSV file.
 * @param {string} filename  e.g. "share-statement.csv"
 * @param {string[]} headers column titles
 * @param {Array<Array>} rows  array of row arrays (same length as headers)
 */
export function exportToCsv(filename, headers, rows) {
  const lines = [headers.map(escapeCell).join(',')];
  for (const r of rows) lines.push(r.map(escapeCell).join(','));
  const csv = '﻿' + lines.join('\r\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
