import { useState } from 'react';
import { Users, PiggyBank, Landmark, Coins, AlertTriangle, TrendingUp, BarChart3, Wallet } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Input from '../../components/ui/Input';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useApi } from '../../hooks/useApi';
import { reportsService } from '../../services/reports';
import toast from 'react-hot-toast';

const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

export default function AnalyticsPage() {
  const { data: kpis, loading } = useApi(() => reportsService.dashboardKPIs());

  const cards = kpis ? [
    { label: 'Total Members', value: kpis.total_members, icon: Users, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/30' },
    { label: 'Active Deposits', value: kpis.active_deposits, icon: PiggyBank, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/30' },
    { label: 'Deposit Balance', value: fmt(kpis.total_deposit_balance), icon: Wallet, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/30' },
    { label: 'Active Loans', value: kpis.active_loans, icon: Landmark, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/30' },
    { label: 'Loan Outstanding', value: fmt(kpis.total_loan_outstanding), icon: TrendingUp, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/30' },
    { label: 'Overdue EMIs', value: kpis.overdue_emis, icon: AlertTriangle, color: kpis.overdue_emis > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-400', bg: kpis.overdue_emis > 0 ? 'bg-red-50 dark:bg-red-900/30' : 'bg-gray-50 dark:bg-gray-800/30' },
    { label: 'Share Capital', value: fmt(kpis.total_share_capital), icon: Coins, color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-50 dark:bg-purple-900/30' },
    { label: 'Active Schemes', value: kpis.active_schemes, icon: BarChart3, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/30' },
  ] : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Analytics Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Society-wide KPIs and financial health</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {loading
          ? Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)
          : cards.map(stat => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.label}</p>
                    <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">{stat.value}</p>
                  </div>
                  <div className={`rounded-lg p-2.5 ${stat.bg}`}><Icon className={`h-5 w-5 ${stat.color}`} /></div>
                </div>
              </Card>
            );
          })}
      </div>

      {kpis?.deposit_to_loan_ratio != null && (
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Deposit to Loan Ratio</p>
              <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-gray-100">{kpis.deposit_to_loan_ratio}x</p>
            </div>
            <Badge color={kpis.deposit_to_loan_ratio >= 1 ? 'green' : 'red'}>
              {kpis.deposit_to_loan_ratio >= 1 ? 'Healthy' : 'At Risk'}
            </Badge>
          </div>
        </Card>
      )}

      <DividendCalculator />
    </div>
  );
}

function DividendCalculator() {
  const [rate, setRate] = useState('');
  const [year, setYear] = useState('2025-26');
  const [post, setPost] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleCalc = async () => {
    if (!rate || !year) { toast.error('Enter rate and year'); return; }
    setLoading(true);
    try {
      const res = await reportsService.calculateDividend(Number(rate), year, post);
      setResult(res);
      if (post) toast.success(`Dividends of ${fmt(res.total_dividend)} posted for ${res.shareholders} members`);
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  return (
    <Card>
      <CardHeader><CardTitle>Dividend Calculator</CardTitle></CardHeader>
      <div className="space-y-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <Input label="Dividend Rate (%)" type="number" step="0.01" min="0" value={rate} onChange={e => setRate(e.target.value)} />
          <Input label="Financial Year" value={year} onChange={e => setYear(e.target.value)} placeholder="e.g. 2025-26" />
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input type="checkbox" checked={post} onChange={e => setPost(e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary-600" />
            Post to Ledger
          </label>
          <Button loading={loading} onClick={handleCalc}>Calculate</Button>
        </div>

        {result && (
          <div className="space-y-3">
            <div className="flex gap-4 text-sm">
              <span className="text-gray-500">Total Dividend: <strong className="text-emerald-600">{fmt(result.total_dividend)}</strong></span>
              <span className="text-gray-500">Shareholders: <strong>{result.shareholders}</strong></span>
              {result.posted && <Badge color="green">Posted</Badge>}
            </div>
            <div className="max-h-60 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-gray-50 dark:bg-gray-800/50">
                  <tr>
                    <th className="px-3 py-2 text-gray-600 dark:text-gray-400">Member</th>
                    <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">Shares</th>
                    <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">Value</th>
                    <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">Dividend</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {result.results.map((r, i) => (
                    <tr key={i} className="bg-white dark:bg-gray-900">
                      <td className="px-3 py-2 font-medium">{r.member_name}</td>
                      <td className="px-3 py-2 text-right">{r.shares}</td>
                      <td className="px-3 py-2 text-right">{fmt(r.share_value)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-emerald-600">{fmt(r.dividend_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
