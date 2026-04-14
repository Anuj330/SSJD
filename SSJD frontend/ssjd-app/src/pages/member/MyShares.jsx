import { Coins } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import EmptyState from '../../components/ui/EmptyState';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useApi } from '../../hooks/useApi';
import { sharesService } from '../../services/shares';
import { useAuthStore } from '../../store/authStore';

const txnColors = { purchase: 'green', refund: 'red', transfer: 'blue', dividend: 'purple' };

export default function MyShares() {
  const { memberId } = useAuthStore();
  const { data, loading } = useApi(() => sharesService.getMemberShares(memberId));

  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  if (loading) return <div className="space-y-4"><CardSkeleton /><CardSkeleton /></div>;

  const totalShares = data?.total_shares ?? 0;
  const totalValue = data?.total_value ?? 0;
  const faceValue = data?.face_value_per_share ?? 10;
  const txns = data?.transactions ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">My Shares</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Your share capital holdings</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Shares</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">{totalShares}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Face Value / Share</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">{fmt(faceValue)}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Value</p>
          <p className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{fmt(totalValue)}</p>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Transaction History</CardTitle></CardHeader>
        {txns.length === 0
          ? <EmptyState icon={Coins} title="No share transactions" description="You haven't purchased any shares yet." />
          : (
            <div className="max-h-72 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-gray-50 dark:bg-gray-800/50">
                  <tr>
                    <th className="px-3 py-2 text-gray-600 dark:text-gray-400">Date</th>
                    <th className="px-3 py-2 text-gray-600 dark:text-gray-400">Type</th>
                    <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">Shares</th>
                    <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {txns.map((t, i) => (
                    <tr key={i} className="bg-white dark:bg-gray-900">
                      <td className="px-3 py-2 text-xs">{t.txn_date}</td>
                      <td className="px-3 py-2"><Badge color={txnColors[t.txn_type] || 'gray'}>{t.txn_type}</Badge></td>
                      <td className="px-3 py-2 text-right font-medium">{t.shares > 0 ? `+${t.shares}` : t.shares}</td>
                      <td className="px-3 py-2 text-right font-semibold">{fmt(t.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </Card>
    </div>
  );
}
