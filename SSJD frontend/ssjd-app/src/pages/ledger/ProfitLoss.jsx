import { useState } from 'react';
import { TrendingUp, TrendingDown, Download } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import EmptyState from '../../components/ui/EmptyState';
import { useApi } from '../../hooks/useApi';
import { ledgerService } from '../../services/ledger';
import { exportToCsv } from '../../utils/exportCsv';
import toast from 'react-hot-toast';

const fmt = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(Number(n) || 0);

export default function ProfitLoss() {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const { data, loading } = useApi(() => ledgerService.getProfitLoss(from || undefined, to || undefined), [from, to]);

  const income = data?.income ?? [];   // groups: [{category, subtotal, accounts:[...]}]
  const expense = data?.expense ?? [];
  const net = Number(data?.net_profit ?? 0);
  const surplus = net >= 0;

  const handleExport = () => {
    if (!data) return toast.error('Nothing to export');
    const groupRows = (groups) => groups.flatMap((g) => [
      [g.category, '', Number(g.subtotal).toFixed(2)],
      ...g.accounts.map((a) => [`   ${a.account_name}`, a.account_code, Number(a.amount).toFixed(2)]),
    ]);
    const rows = [
      ['INCOME', '', ''],
      ...groupRows(income),
      ['Total Income', '', Number(data.total_income).toFixed(2)],
      ['', '', ''],
      ['EXPENSES', '', ''],
      ...groupRows(expense),
      ['Total Expenses', '', Number(data.total_expense).toFixed(2)],
      ['', '', ''],
      [surplus ? 'Net Surplus' : 'Net Deficit', '', net.toFixed(2)],
    ];
    exportToCsv('profit-and-loss.csv', ['Account / Category', 'Code', 'Amount (INR)'], rows);
    toast.success('Exported');
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">Profit &amp; Loss</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Income &amp; Expenditure statement for a period.</p>
        </div>
        <div className="flex items-end gap-2">
          <Input label="From" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          <Input label="To" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
          <Button variant="outline" onClick={handleExport} className="mb-0.5"><Download className="h-4 w-4" /> Export</Button>
        </div>
      </div>

      {loading ? (
        <Card><div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />)}</div></Card>
      ) : !data ? (
        <Card><EmptyState icon={TrendingUp} title="No data" description="No ledger entries for this period." /></Card>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat tone="emerald" label="Total Income" value={fmt(data.total_income)} icon={TrendingUp} />
            <Stat tone="amber" label="Total Expenses" value={fmt(data.total_expense)} icon={TrendingDown} />
            <Stat tone={surplus ? 'emerald' : 'red'} label={surplus ? 'Net Surplus' : 'Net Deficit'} value={fmt(Math.abs(net))} icon={surplus ? TrendingUp : TrendingDown} big />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Section title="Income" groups={income} total={data.total_income} tone="emerald" />
            <Section title="Expenses" groups={expense} total={data.total_expense} tone="amber" />
          </div>

          <Card>
            <div className="flex items-center justify-between">
              <span className="text-base font-bold text-gray-900 dark:text-gray-100">{surplus ? 'Net Surplus' : 'Net Deficit'}</span>
              <span className={`num text-xl font-bold ${surplus ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>{fmt(Math.abs(net))}</span>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function Section({ title, groups, total, tone }) {
  const totalColor = tone === 'emerald' ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400';
  return (
    <Card className="!p-0">
      <div className="border-b border-gray-200 px-4 py-3 dark:border-gray-800"><span className="font-bold text-gray-900 dark:text-gray-100">{title}</span></div>
      {groups.length === 0 ? <div className="px-4 py-6 text-center text-sm text-gray-400">No {title.toLowerCase()} recorded.</div> :
        groups.map((g) => (
          <div key={g.category} className="border-b border-gray-100 dark:border-gray-800/60">
            {/* Category head with subtotal */}
            <div className="flex items-center justify-between bg-gray-50 px-4 py-2 dark:bg-gray-800/40">
              <span className="text-[13px] font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">{g.category}</span>
              <span className="num text-sm font-semibold text-gray-700 dark:text-gray-300">{fmt(g.subtotal)}</span>
            </div>
            {/* Accounts within the category */}
            {g.accounts.map((a) => (
              <div key={a.account_code} className="flex items-center justify-between px-4 py-2 pl-6 text-sm">
                <span className="text-gray-600 dark:text-gray-400">{a.account_name} <span className="font-mono text-xs text-gray-400">{a.account_code}</span></span>
                <span className="num text-gray-900 dark:text-gray-100">{fmt(a.amount)}</span>
              </div>
            ))}
          </div>
        ))}
      <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3 dark:border-gray-800">
        <span className="font-bold text-gray-900 dark:text-gray-100">Total {title}</span>
        <span className={`num font-bold ${totalColor}`}>{fmt(total)}</span>
      </div>
    </Card>
  );
}

function Stat({ icon: Icon, label, value, tone, big }) {
  const tones = {
    emerald: 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300',
    amber: 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-300',
    red: 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-300',
  };
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${tones[tone]}`}><Icon className="h-5 w-5" /></span>
      <div><div className="text-xs text-gray-500 dark:text-gray-400">{label}</div><div className={`num font-bold text-gray-900 dark:text-gray-100 ${big ? 'text-2xl' : 'text-xl'}`}>{value}</div></div>
    </div>
  );
}
