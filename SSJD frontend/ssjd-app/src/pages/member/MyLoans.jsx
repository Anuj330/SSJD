import { useState } from 'react';
import { Landmark, Calendar, Download, CreditCard } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import DataTable from '../../components/ui/DataTable';
import EmptyState from '../../components/ui/EmptyState';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Modal from '../../components/ui/Modal';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useApi } from '../../hooks/useApi';
import { useRazorpay } from '../../hooks/useRazorpay';
import { loansService } from '../../services/loans';
import { useAuthStore } from '../../store/authStore';

const statusColors = { applied: 'yellow', approved: 'blue', rejected: 'red', disbursed: 'purple', active: 'green', closed: 'gray', defaulted: 'red' };

export default function MyLoans() {
  const { token } = useAuthStore();
  const { data: loans, loading, execute: refresh } = useApi(() => loansService.list());
  const [scheduleModal, setScheduleModal] = useState(null);
  const [payModal, setPayModal] = useState(null);
  const [payAmount, setPayAmount] = useState('');
  const [nextEmi, setNextEmi] = useState(null);
  const { pay, loading: paying } = useRazorpay();

  // Open the Pay modal and auto-fill with the next unpaid EMI (still editable).
  const openPay = async (row) => {
    setPayModal(row);
    setPayAmount('');
    setNextEmi(null);
    try {
      const sch = await loansService.getSchedule(row.id);
      const next = (sch?.schedule || []).find(r => !r.is_paid);
      if (next) {
        // amount_due already includes the accrued ₹10/month late fee
        const remaining = Number(next.amount_due ?? (Number(next.total_due) - Number(next.total_paid || 0)));
        setPayAmount(String(Math.round(remaining * 100) / 100));
        setNextEmi({ ...next, remaining, penalty: Number(next.penalty || 0) });
      }
    } catch { /* leave blank on error */ }
  };

  const list = loans ?? [];
  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const totalOutstanding = list.reduce((s, l) => s + Number(l.outstanding_principal || 0), 0);
  const activeLoans = list.filter(l => l.status === 'active').length;

  const handlePayEmi = () => {
    const amt = Number(payAmount);
    if (!amt || amt <= 0) return;
    pay('loan_repayment', payModal.id, amt, () => {
      setPayModal(null);
      setPayAmount('');
      refresh();
    });
  };

  const columns = [
    { key: 'loan_number', label: 'Loan #', render: v => <span className="font-mono text-xs font-medium">{v}</span> },
    { key: 'product_name', label: 'Product' },
    { key: 'disbursed_amount', label: 'Disbursed', render: v => v > 0 ? fmt(v) : '-' },
    { key: 'outstanding_principal', label: 'Outstanding', render: v => <span className="font-semibold text-amber-600 dark:text-amber-400">{fmt(v)}</span> },
    { key: 'interest_rate', label: 'Rate', render: v => `${Number(v).toFixed(2)}%` },
    { key: 'tenure_months', label: 'Tenure', render: v => `${v}m` },
    { key: 'status', label: 'Status', render: v => <Badge color={statusColors[v] || 'gray'}>{v}</Badge> },
    { key: 'id', label: '', sortable: false, render: (_, row) => (
      <div className="flex gap-1">
        {row.status === 'active' && (
          <Button variant="outline" size="sm" title="Pay EMI Online" onClick={e => { e.stopPropagation(); openPay(row); }}>
            <CreditCard className="h-3.5 w-3.5" /> Pay
          </Button>
        )}
        {['active', 'closed'].includes(row.status) && (
          <Button variant="ghost" size="sm" title="View EMI Schedule" onClick={e => { e.stopPropagation(); setScheduleModal(row); }}>
            <Calendar className="h-3.5 w-3.5 text-blue-500" />
          </Button>
        )}
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">My Loans</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Your loan accounts and repayment status</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Loans</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">{list.length}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Active Loans</p>
          <p className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{activeLoans}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Outstanding</p>
          <p className="mt-1 text-2xl font-bold text-amber-600 dark:text-amber-400">{fmt(totalOutstanding)}</p>
        </Card>
      </div>

      <Card>
        {!loading && list.length === 0
          ? <EmptyState icon={Landmark} title="No loans" description="You don't have any loan accounts." />
          : <DataTable columns={columns} data={list} loading={loading} onRowClick={row => ['active', 'closed'].includes(row.status) && setScheduleModal(row)} />}
      </Card>

      {scheduleModal && (
        <Modal isOpen onClose={() => setScheduleModal(null)} title={`EMI Schedule — ${scheduleModal.loan_number}`} size="xl">
          <LoanSchedule loanId={scheduleModal.id} token={token} />
        </Modal>
      )}

      {payModal && (
        <Modal isOpen onClose={() => setPayModal(null)} title={`Pay EMI — ${payModal.loan_number}`} size="sm">
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Outstanding: <strong className="text-amber-600">{fmt(payModal.outstanding_principal)}</strong>
            </p>
            {nextEmi && (
              <div className="rounded-lg bg-primary-50 px-3 py-2 text-sm dark:bg-primary-900/20">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-300">Next EMI #{nextEmi.installment_no} · due {nextEmi.due_date}</span>
                  <span className="font-bold text-primary-700 dark:text-primary-300">{fmt(nextEmi.remaining)}</span>
                </div>
                {nextEmi.penalty > 0 && (
                  <div className="mt-1 text-xs font-medium text-red-600 dark:text-red-400">
                    Includes late fee of {fmt(nextEmi.penalty)} (₹10/month overdue)
                  </div>
                )}
              </div>
            )}
            <Input label="Payment Amount (INR)" type="number" min="1" placeholder="Enter EMI amount" value={payAmount} onChange={e => setPayAmount(e.target.value)} />
            <p className="text-xs text-gray-400">Auto-filled with your next EMI — edit if you want to pay a different amount.</p>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setPayModal(null)}>Cancel</Button>
              <Button loading={paying} disabled={!payAmount || Number(payAmount) <= 0} onClick={handlePayEmi}>
                <CreditCard className="h-4 w-4" /> Pay {payAmount ? fmt(Number(payAmount)) : ''}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

function LoanSchedule({ loanId, token }) {
  const { data, loading } = useApi(() => loansService.getSchedule(loanId));
  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  if (loading) return <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />)}</div>;

  const rows = data?.schedule ?? [];
  if (!rows.length) return <p className="py-4 text-center text-sm text-gray-500">No schedule generated yet.</p>;

  const apiBase = import.meta.env.VITE_API_BASE || '/api/v1';

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <a href={`${apiBase}/pdf/loan-schedule/${loanId}`}
           target="_blank" rel="noopener noreferrer"
           className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-800">
          <Download className="h-3.5 w-3.5" /> Download PDF
        </a>
      </div>
      <div className="max-h-96 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 border-b bg-gray-50 dark:bg-gray-800/50">
            <tr>
              <th className="px-3 py-2 font-medium text-gray-600 dark:text-gray-400">#</th>
              <th className="px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Due Date</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600 dark:text-gray-400">Principal</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600 dark:text-gray-400">Interest</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600 dark:text-gray-400">EMI</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600 dark:text-gray-400">Paid</th>
              <th className="px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {rows.map(r => (
              <tr key={r.installment_no} className={`bg-white dark:bg-gray-900 ${r.is_overdue ? 'bg-red-50/50 dark:bg-red-900/10' : ''}`}>
                <td className="px-3 py-2 text-gray-500">{r.installment_no}</td>
                <td className="px-3 py-2">{r.due_date}</td>
                <td className="px-3 py-2 text-right">{fmt(r.principal_due)}</td>
                <td className="px-3 py-2 text-right text-blue-600">{fmt(r.interest_due)}</td>
                <td className="px-3 py-2 text-right font-medium">{fmt(r.total_due)}</td>
                <td className="px-3 py-2 text-right">{r.total_paid > 0 ? fmt(r.total_paid) : '-'}</td>
                <td className="px-3 py-2">
                  {r.is_paid ? <Badge color="green">Paid</Badge> : r.is_overdue ? <Badge color="red">Overdue</Badge> : <Badge color="yellow">Pending</Badge>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
