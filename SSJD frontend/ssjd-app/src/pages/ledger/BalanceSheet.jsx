import { useState } from 'react';
import { Scale, Download, CheckCircle2, AlertTriangle } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import EmptyState from '../../components/ui/EmptyState';
import { useApi } from '../../hooks/useApi';
import { ledgerService } from '../../services/ledger';
import { exportToCsv } from '../../utils/exportCsv';
import toast from 'react-hot-toast';

const fmt = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(Number(n) || 0);

export default function BalanceSheet() {
  const [asOf, setAsOf] = useState('');
  const { data, loading } = useApi(() => ledgerService.getBalanceSheet(asOf || undefined), [asOf]);

  const assets = data?.assets ?? [];
  const liabilities = data?.liabilities ?? [];
  const equity = data?.equity ?? [];
  const surplus = Number(data?.current_surplus ?? 0);

  const handleExport = () => {
    if (!data) return toast.error('Nothing to export');
    const rows = [
      ['ASSETS', ''],
      ...assets.map((r) => [r.account_name, Number(r.amount).toFixed(2)]),
      ['Total Assets', Number(data.total_assets).toFixed(2)],
      ['', ''],
      ['LIABILITIES', ''],
      ...liabilities.map((r) => [r.account_name, Number(r.amount).toFixed(2)]),
      ['Total Liabilities', Number(data.total_liabilities).toFixed(2)],
      ['', ''],
      ['EQUITY', ''],
      ...equity.map((r) => [r.account_name, Number(r.amount).toFixed(2)]),
      ['Current Surplus/Deficit', surplus.toFixed(2)],
      ['Total Liabilities + Equity', Number(data.total_liabilities_and_equity).toFixed(2)],
    ];
    exportToCsv('balance-sheet.csv', ['Item', 'Amount (INR)'], rows);
    toast.success('Exported');
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">Balance Sheet</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Financial position — Assets vs Liabilities + Equity.</p>
        </div>
        <div className="flex items-end gap-2">
          <Input label="As of" type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} />
          <Button variant="outline" onClick={handleExport} className="mb-0.5"><Download className="h-4 w-4" /> Export</Button>
        </div>
      </div>

      {loading ? (
        <Card><div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />)}</div></Card>
      ) : !data ? (
        <Card><EmptyState icon={Scale} title="No data" description="No ledger entries yet." /></Card>
      ) : (
        <>
          <div className={`flex items-center gap-2 rounded-xl border p-3 text-sm ${data.is_balanced ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-900/20 dark:text-emerald-300' : 'border-red-200 bg-red-50 text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-300'}`}>
            {data.is_balanced ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            {data.is_balanced
              ? <>Balanced — Assets <strong className="num">{fmt(data.total_assets)}</strong> = Liabilities + Equity <strong className="num">{fmt(data.total_liabilities_and_equity)}</strong></>
              : <>Out of balance — Assets {fmt(data.total_assets)} vs L+E {fmt(data.total_liabilities_and_equity)}</>}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Section title="Assets" rows={assets} total={data.total_assets} totalLabel="Total Assets" />
            <div className="space-y-4">
              <Section title="Liabilities" rows={liabilities} total={data.total_liabilities} totalLabel="Total Liabilities" />
              <Section
                title="Equity"
                rows={[...equity, { account_code: '—', account_name: 'Current Surplus / (Deficit)', amount: surplus }]}
                total={data.total_liabilities_and_equity - data.total_liabilities}
                totalLabel="Total Equity"
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Section({ title, rows, total, totalLabel }) {
  return (
    <Card className="!p-0">
      <div className="border-b border-gray-200 px-4 py-3 dark:border-gray-800"><span className="font-bold text-gray-900 dark:text-gray-100">{title}</span></div>
      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {rows.length === 0 ? <div className="px-4 py-6 text-center text-sm text-gray-400">None.</div> :
          rows.map((r, i) => (
            <div key={r.account_code + i} className="flex items-center justify-between px-4 py-2.5 text-sm">
              <span className="text-gray-700 dark:text-gray-300">{r.account_name} {r.account_code !== '—' && <span className="font-mono text-xs text-gray-400">{r.account_code}</span>}</span>
              <span className="num font-medium text-gray-900 dark:text-gray-100">{fmt(r.amount)}</span>
            </div>
          ))}
      </div>
      <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3 dark:border-gray-800">
        <span className="font-bold text-gray-900 dark:text-gray-100">{totalLabel}</span>
        <span className="num font-bold text-gray-900 dark:text-gray-100">{fmt(total)}</span>
      </div>
    </Card>
  );
}
