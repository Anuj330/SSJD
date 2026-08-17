import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

const TONES = {
  emerald: { chip: 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300', glow: 'rgba(14,159,110,.16)' },
  blue: { chip: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300', glow: 'rgba(59,111,212,.16)' },
  violet: { chip: 'bg-violet-50 text-violet-600 dark:bg-violet-900/30 dark:text-violet-300', glow: 'rgba(124,92,224,.16)' },
  amber: { chip: 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-300', glow: 'rgba(201,130,27,.18)' },
};

/**
 * KPI card: label, big value, icon chip, optional delta + sub-text, soft radial glow.
 * delta: { dir: 'up'|'down', text }
 */
export default function StatCard({ label, value, icon: Icon, tone = 'emerald', delta, sub }) {
  const t = TONES[tone] || TONES.emerald;
  return (
    <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <div
        className="pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full"
        style={{ background: `radial-gradient(circle at 70% 30%, ${t.glow}, transparent 70%)` }}
      />
      <div className="relative flex items-start justify-between">
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
        {Icon && (
          <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${t.chip}`}>
            <Icon className="h-[18px] w-[18px]" />
          </span>
        )}
      </div>
      <p className="num relative mt-3 text-3xl font-bold leading-none text-gray-900 dark:text-gray-100">{value}</p>
      {(delta || sub) && (
        <div className="relative mt-3 flex items-center gap-2 text-xs">
          {delta && (
            <span
              className={`num inline-flex items-center gap-0.5 font-bold ${
                delta.dir === 'down' ? 'text-red-500 dark:text-red-400' : 'text-primary-600 dark:text-primary-400'
              }`}
            >
              {delta.dir === 'down' ? <ArrowDownRight className="h-3.5 w-3.5" /> : <ArrowUpRight className="h-3.5 w-3.5" />}
              {delta.text}
            </span>
          )}
          {sub && <span className="text-gray-400 dark:text-gray-500">{sub}</span>}
        </div>
      )}
    </div>
  );
}
