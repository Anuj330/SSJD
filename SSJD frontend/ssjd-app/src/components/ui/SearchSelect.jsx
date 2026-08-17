import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Search } from 'lucide-react';

/**
 * Searchable single-select combobox — a drop-in for large option lists
 * (e.g. 500+ members). Type to filter by label. Calls onChange(value).
 */
export default function SearchSelect({ label, value, onChange, options = [], placeholder = 'Select…', error }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const ref = useRef(null);
  const selected = options.find((o) => String(o.value) === String(value));

  useEffect(() => {
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  const q = query.trim().toLowerCase();
  const filtered = q ? options.filter((o) => o.label.toLowerCase().includes(q)) : options;
  const shown = filtered.slice(0, 200);

  const pick = (o) => { onChange?.(o.value); setOpen(false); setQuery(''); };

  return (
    <div className="space-y-1" ref={ref}>
      {label && <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>}
      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className={`flex w-full items-center justify-between rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm transition-colors focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 ${error ? '!border-red-500' : ''}`}
        >
          <span className={`truncate ${selected ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400'}`}>
            {selected ? selected.label : placeholder}
          </span>
          <ChevronDown className={`h-4 w-4 flex-none text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
        </button>

        {open && (
          <div className="absolute z-50 mt-1 w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
            <div className="p-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  autoFocus
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search name or number…"
                  className="w-full rounded-md border border-gray-300 bg-white py-1.5 pl-8 pr-2 text-sm text-gray-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
                />
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto pb-1">
              {shown.length === 0 ? (
                <div className="px-3 py-3 text-sm text-gray-400">No matches</div>
              ) : (
                shown.map((o) => (
                  <button
                    key={o.value}
                    type="button"
                    onClick={() => pick(o)}
                    className={`block w-full truncate px-3 py-2 text-left text-sm text-gray-800 hover:bg-primary-50 dark:text-gray-100 dark:hover:bg-gray-700 ${String(o.value) === String(value) ? 'bg-primary-50 font-semibold dark:bg-gray-700' : ''}`}
                  >
                    {o.label}
                  </button>
                ))
              )}
              {filtered.length > shown.length && (
                <div className="px-3 py-2 text-xs text-gray-400">Showing first 200 — refine your search</div>
              )}
            </div>
          </div>
        )}
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
