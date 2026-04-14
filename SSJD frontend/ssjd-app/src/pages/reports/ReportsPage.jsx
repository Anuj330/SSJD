import { useState } from 'react';
import { BarChart3, FileText, DollarSign, Users, Calculator, Activity, Receipt, Download } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Input from '../../components/ui/Input';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useApi } from '../../hooks/useApi';
import { reportsService } from '../../services/reports';
import toast from 'react-hot-toast';

const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

export default function ReportsPage() {
  const [tab, setTab] = useState('pnl');

  const tabs = [
    { key: 'pnl', label: 'Profit & Loss', icon: BarChart3 },
    { key: 'bs', label: 'Balance Sheet', icon: FileText },
    { key: 'cf', label: 'Cash Flow', icon: DollarSign },
    { key: 'outstanding', label: 'Member Outstanding', icon: Users },
    { key: 'batch', label: 'Batch Interest', icon: Calculator },
    { key: 'activity', label: 'Activity Log', icon: Activity },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Reports & Analytics</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Financial reports, member analytics, and batch operations</p>
      </div>

      <div className="flex flex-wrap gap-1 border-b border-gray-200 dark:border-gray-700">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium transition-colors ${tab === t.key ? 'border-b-2 border-primary-600 text-primary-600 dark:text-primary-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'}`}>
              <Icon className="h-4 w-4" />{t.label}
            </button>
          );
        })}
      </div>

      {tab === 'pnl' && <ProfitLoss />}
      {tab === 'bs' && <BalanceSheet />}
      {tab === 'cf' && <CashFlow />}
      {tab === 'outstanding' && <MemberOutstanding />}
      {tab === 'batch' && <BatchInterest />}
      {tab === 'activity' && <ActivityLogs />}
    </div>
  );
}

function ProfitLoss() {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const { data, loading, execute } = useApi(() => reportsService.profitLoss(from || undefined, to || undefined), [from, to]);

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <Input label="From" type="date" value={from} onChange={e => setFrom(e.target.value)} />
          <Input label="To" type="date" value={to} onChange={e => setTo(e.target.value)} />
          {data && <a href={`/api/v1/pdf/profit-loss${from ? `?from_date=${from}` : ''}${to ? `${from ? '&' : '?'}to_date=${to}` : ''}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-400"><Download className="h-4 w-4" /> PDF</a>}
        </div>
      </Card>
      {loading ? <CardSkeleton /> : data && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader><CardTitle>Income</CardTitle><span className="text-lg font-bold text-emerald-600">{fmt(data.total_income)}</span></CardHeader>
            {data.income.map((r, i) => <div key={i} className="flex justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50"><span className="text-sm">{r.name}</span><span className="text-sm font-medium text-emerald-600">{fmt(r.amount)}</span></div>)}
            {data.income.length === 0 && <p className="text-sm text-gray-400">No income entries</p>}
          </Card>
          <Card>
            <CardHeader><CardTitle>Expenses</CardTitle><span className="text-lg font-bold text-amber-600">{fmt(data.total_expenses)}</span></CardHeader>
            {data.expenses.map((r, i) => <div key={i} className="flex justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50"><span className="text-sm">{r.name}</span><span className="text-sm font-medium text-amber-600">{fmt(r.amount)}</span></div>)}
            {data.expenses.length === 0 && <p className="text-sm text-gray-400">No expense entries</p>}
          </Card>
          <Card className="lg:col-span-2">
            <div className="flex items-center justify-between">
              <span className="text-lg font-semibold">Net Profit / Loss</span>
              <span className={`text-2xl font-bold ${Number(data.net_profit) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{fmt(data.net_profit)}</span>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

function BalanceSheet() {
  const { data, loading } = useApi(() => reportsService.balanceSheet());

  if (loading) return <CardSkeleton />;
  if (!data) return null;

  const Section = ({ title, items, total, color }) => (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle><span className={`text-lg font-bold ${color}`}>{fmt(total)}</span></CardHeader>
      <div className="space-y-1">
        {items.map((r, i) => <div key={i} className="flex justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50"><span className="text-sm">{r.name} <span className="text-xs text-gray-400">({r.code})</span></span><span className={`text-sm font-medium ${color}`}>{fmt(r.balance)}</span></div>)}
        {items.length === 0 && <p className="text-sm text-gray-400">No entries</p>}
      </div>
    </Card>
  );

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <a href="/api/v1/pdf/balance-sheet" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-400"><Download className="h-4 w-4" /> Download PDF</a>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Section title="Assets" items={data.assets} total={data.total_assets} color="text-blue-600 dark:text-blue-400" />
        <Section title="Liabilities" items={data.liabilities} total={data.total_liabilities} color="text-amber-600 dark:text-amber-400" />
        <Section title="Equity" items={data.equity} total={data.total_equity} color="text-purple-600 dark:text-purple-400" />
      </div>
      <Card>
        <div className="flex items-center justify-between">
          <span className="font-semibold">Balance Check (A = L + E)</span>
          <Badge color={data.is_balanced ? 'green' : 'red'}>{data.is_balanced ? 'Balanced' : 'Unbalanced'}</Badge>
        </div>
      </Card>
    </div>
  );
}

function CashFlow() {
  const { data, loading } = useApi(() => reportsService.cashFlow());
  if (loading) return <CardSkeleton />;
  if (!data) return null;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader><CardTitle>Cash Inflows</CardTitle><span className="text-lg font-bold text-emerald-600">{fmt(data.total_inflow)}</span></CardHeader>
        {data.inflows.map((r, i) => <div key={i} className="flex justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50"><span className="text-sm">{r.txn_type}</span><span className="text-sm font-medium text-emerald-600">{fmt(r.amount)}</span></div>)}
      </Card>
      <Card>
        <CardHeader><CardTitle>Cash Outflows</CardTitle><span className="text-lg font-bold text-amber-600">{fmt(data.total_outflow)}</span></CardHeader>
        {data.outflows.map((r, i) => <div key={i} className="flex justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50"><span className="text-sm">{r.txn_type}</span><span className="text-sm font-medium text-amber-600">{fmt(r.amount)}</span></div>)}
      </Card>
      <Card className="lg:col-span-2">
        <div className="flex items-center justify-between"><span className="font-semibold">Net Cash Flow</span><span className={`text-2xl font-bold ${Number(data.net_flow) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{fmt(data.net_flow)}</span></div>
      </Card>
    </div>
  );
}

function MemberOutstanding() {
  const { data, loading } = useApi(() => reportsService.memberOutstanding());
  if (loading) return <CardSkeleton />;
  const list = data?.members ?? [];

  return (
    <Card className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-gray-50 dark:bg-gray-800/50">
            <tr>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Member</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">Deposits</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">Loans</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">Shares</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">Net Position</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-600 dark:text-gray-400">Overdue EMIs</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {list.map(m => (
              <tr key={m.member_id} className="bg-white dark:bg-gray-900">
                <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{m.member_name} <span className="text-xs text-gray-400">#{m.member_id}</span></td>
                <td className="px-4 py-3 text-right text-emerald-600 dark:text-emerald-400">{fmt(m.total_deposits)}</td>
                <td className="px-4 py-3 text-right text-amber-600 dark:text-amber-400">{fmt(m.total_loans)}</td>
                <td className="px-4 py-3 text-right text-purple-600 dark:text-purple-400">{fmt(m.total_shares)}</td>
                <td className="px-4 py-3 text-right"><span className={`font-bold ${Number(m.net_position) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{fmt(m.net_position)}</span></td>
                <td className="px-4 py-3 text-center">{m.overdue_emis > 0 ? <Badge color="red">{m.overdue_emis}</Badge> : <span className="text-gray-300">0</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function BatchInterest() {
  const [asOf, setAsOf] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    try {
      const res = await reportsService.batchInterest(asOf || undefined);
      setResult(res);
      toast.success(`Processed ${res.processed} deposits`);
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <Card>
        <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">Calculate and post accrued interest for <strong>all active deposits</strong> in one batch.</p>
        <div className="flex gap-4 items-end">
          <Input label="As Of Date (optional)" type="date" value={asOf} onChange={e => setAsOf(e.target.value)} />
          <Button loading={loading} onClick={handleRun}>Run Batch Interest</Button>
        </div>
      </Card>
      {result && (
        <Card>
          <CardHeader><CardTitle>Results</CardTitle><Badge color="green">{result.processed} processed</Badge></CardHeader>
          {result.results.map((r, i) => (
            <div key={i} className="flex justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50">
              <span className="text-sm font-mono">{r.account_number}</span>
              <span className="text-sm"><span className="text-gray-400">{r.days} days →</span> <span className="font-semibold text-emerald-600">{fmt(r.interest)}</span></span>
            </div>
          ))}
          {result.errors > 0 && <p className="text-sm text-red-500">{result.errors} errors occurred</p>}
        </Card>
      )}
    </div>
  );
}

function ActivityLogs() {
  const { data, loading } = useApi(() => reportsService.activityLogs({ limit: 50 }));
  const logs = data?.logs ?? [];

  if (loading) return <CardSkeleton />;

  return (
    <Card className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-gray-50 dark:bg-gray-800/50">
            <tr>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Time</th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">User</th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Action</th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Entity</th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Detail</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {logs.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-12 text-center text-gray-500">No activity logs yet.</td></tr>
            ) : logs.map(l => (
              <tr key={l.id} className="bg-white dark:bg-gray-900">
                <td className="whitespace-nowrap px-4 py-2 text-xs text-gray-500">{l.created_at ? new Date(l.created_at).toLocaleString('en-IN') : '-'}</td>
                <td className="px-4 py-2"><Badge color={l.user_role === 'admin' ? 'blue' : 'green'}>{l.user_sub}</Badge></td>
                <td className="px-4 py-2 font-medium">{l.action}</td>
                <td className="px-4 py-2 text-gray-500">{l.entity_type} {l.entity_id && `#${l.entity_id}`}</td>
                <td className="max-w-[200px] truncate px-4 py-2 text-xs text-gray-400">{l.detail || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
