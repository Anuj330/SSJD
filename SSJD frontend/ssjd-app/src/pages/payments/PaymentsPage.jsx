import { Receipt } from 'lucide-react';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import DataTable from '../../components/ui/DataTable';
import EmptyState from '../../components/ui/EmptyState';
import { useApi } from '../../hooks/useApi';
import { paymentsService } from '../../services/payments';

const statusColors = { created: 'yellow', paid: 'green', failed: 'red', refunded: 'purple' };
const purposeLabels = {
  deposit: 'Deposit', loan_repayment: 'Loan Repayment',
  share_purchase: 'Share Money', rd_installment: 'RD Installment',
};
const purposeColors = {
  deposit: 'blue', loan_repayment: 'purple', share_purchase: 'green', rd_installment: 'cyan',
};

const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);
const initials = (s = '') => s.trim().split(/\s+/).slice(0, 2).map(w => w[0] || '').join('').toUpperCase() || '?';

export default function PaymentsPage() {
  const { data, loading } = useApi(() => paymentsService.list());
  const list = data ?? [];

  const columns = [
    { key: 'id', label: '#', render: v => <span className="text-xs text-gray-400">#{v}</span> },
    { key: 'created_at', label: 'Date', render: v => v ? new Date(v).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : '-' },
    {
      key: 'member_name', label: 'Member', render: (v, row) => (
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-primary-100 text-[10px] font-bold text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">{initials(v)}</span>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{v || 'Unknown'}</div>
            <div className="text-[11px] text-gray-400">#{row.member_id}</div>
          </div>
        </div>
      ),
    },
    { key: 'purpose', label: 'Purpose', render: v => <Badge color={purposeColors[v] || 'gray'}>{purposeLabels[v] || v}</Badge> },
    { key: 'amount', label: 'Amount', render: v => <span className="font-semibold">{fmt(v)}</span> },
    { key: 'razorpay_order_id', label: 'Order ID', render: v => <span className="font-mono text-xs">{v || '-'}</span> },
    { key: 'razorpay_payment_id', label: 'Payment ID', render: v => v ? <span className="font-mono text-xs text-emerald-600">{v}</span> : <span className="text-xs text-gray-400">-</span> },
    { key: 'status', label: 'Status', render: v => <Badge color={statusColors[v] || 'gray'}>{v}</Badge> },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Payment History</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">All online payment transactions via Razorpay</p>
      </div>

      <Card>
        {!loading && list.length === 0
          ? <EmptyState icon={Receipt} title="No payments" description="No online payments have been made yet." />
          : <DataTable columns={columns} data={list} loading={loading} />}
      </Card>
    </div>
  );
}
