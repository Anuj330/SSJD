import { useState } from 'react';
import { PiggyBank, Download, CreditCard } from 'lucide-react';
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
import { depositsService } from '../../services/deposits';
import { useAuthStore } from '../../store/authStore';

const statusColors = { active: 'green', matured: 'blue', closed: 'gray', premature_closed: 'red' };

export default function MyDeposits() {
  const { token } = useAuthStore();
  const { data: deposits, loading, execute: refresh } = useApi(() => depositsService.list());
  const [statementModal, setStatementModal] = useState(null);
  const [payModal, setPayModal] = useState(null);
  const [payAmount, setPayAmount] = useState('');
  const { pay, loading: paying } = useRazorpay();

  const list = deposits ?? [];
  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const totalBalance = list.reduce((s, d) => s + Number(d.current_balance || 0), 0);
  const totalInterest = list.reduce((s, d) => s + Number(d.interest_earned || 0), 0);

  const handlePay = () => {
    const amt = Number(payAmount);
    if (!amt || amt <= 0) return;
    pay('deposit', payModal.id, amt, () => {
      setPayModal(null);
      setPayAmount('');
      refresh();
    });
  };

  const columns = [
    { key: 'account_number', label: 'Account #', render: v => <span className="font-mono text-xs font-medium">{v}</span> },
    { key: 'scheme_name', label: 'Scheme' },
    { key: 'principal_amount', label: 'Principal', render: v => fmt(v) },
    { key: 'interest_earned', label: 'Interest', render: v => <span className="text-blue-600 dark:text-blue-400">{fmt(v)}</span> },
    { key: 'current_balance', label: 'Balance', render: v => <span className="font-semibold text-emerald-600 dark:text-emerald-400">{fmt(v)}</span> },
    { key: 'maturity_date', label: 'Maturity', render: v => v || '-' },
    { key: 'status', label: 'Status', render: v => <Badge color={statusColors[v] || 'gray'}>{v}</Badge> },
    { key: 'id', label: '', sortable: false, render: (_, row) => (
      row.status === 'active' && (
        <Button variant="outline" size="sm" onClick={e => { e.stopPropagation(); setPayModal(row); setPayAmount(''); }}>
          <CreditCard className="h-3.5 w-3.5" /> Pay
        </Button>
      )
    )},
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">My Deposits</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Your deposit accounts and balances</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Accounts</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">{list.length}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Balance</p>
          <p className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{fmt(totalBalance)}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Interest Earned</p>
          <p className="mt-1 text-2xl font-bold text-blue-600 dark:text-blue-400">{fmt(totalInterest)}</p>
        </Card>
      </div>

      <Card>
        {!loading && list.length === 0
          ? <EmptyState icon={PiggyBank} title="No deposits" description="You don't have any deposit accounts yet." />
          : <DataTable columns={columns} data={list} loading={loading} onRowClick={row => setStatementModal(row)} />}
      </Card>

      {statementModal && (
        <Modal isOpen onClose={() => setStatementModal(null)} title={`Statement — ${statementModal.account_number}`} size="xl">
          <DepositStatement depositId={statementModal.id} token={token} />
        </Modal>
      )}

      {payModal && (
        <Modal isOpen onClose={() => setPayModal(null)} title={`Deposit to ${payModal.account_number}`} size="sm">
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Current balance: <strong className="text-emerald-600">{fmt(payModal.current_balance)}</strong>
            </p>
            <Input label="Amount (INR)" type="number" min="1" placeholder="Enter amount" value={payAmount} onChange={e => setPayAmount(e.target.value)} />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setPayModal(null)}>Cancel</Button>
              <Button loading={paying} disabled={!payAmount || Number(payAmount) <= 0} onClick={handlePay}>
                <CreditCard className="h-4 w-4" /> Pay {payAmount ? fmt(Number(payAmount)) : ''}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

function DepositStatement({ depositId, token }) {
  const { data, loading } = useApi(() => depositsService.getStatement(depositId));
  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  if (loading) return <CardSkeleton />;
  if (!data) return null;

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <div className="flex gap-4 text-sm">
          <span className="text-gray-500">Balance: <strong className="text-emerald-600">{fmt(data.current_balance)}</strong></span>
          <span className="text-gray-500">Total Credit: <strong>{fmt(data.total_credit)}</strong></span>
          <span className="text-gray-500">Total Debit: <strong>{fmt(data.total_debit)}</strong></span>
        </div>
      </div>
      <div className="max-h-72 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-gray-50 dark:bg-gray-800/50">
            <tr>
              <th className="px-3 py-2 text-gray-600 dark:text-gray-400">Date</th>
              <th className="px-3 py-2 text-gray-600 dark:text-gray-400">Type</th>
              <th className="px-3 py-2 text-gray-600 dark:text-gray-400">Description</th>
              <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">Debit</th>
              <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">Credit</th>
              <th className="px-3 py-2 text-center text-gray-600 dark:text-gray-400">Receipt</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.rows.map((r, i) => (
              <tr key={i} className="bg-white dark:bg-gray-900">
                <td className="px-3 py-2 text-xs">{r.created_at ? new Date(r.created_at).toLocaleDateString('en-IN') : '-'}</td>
                <td className="px-3 py-2">{r.txn_type}</td>
                <td className="px-3 py-2 text-xs text-gray-500 max-w-[200px] truncate">{r.description}</td>
                <td className="px-3 py-2 text-right text-amber-600">{Number(r.dr_amount) > 0 ? fmt(r.dr_amount) : '-'}</td>
                <td className="px-3 py-2 text-right text-emerald-600">{Number(r.cr_amount) > 0 ? fmt(r.cr_amount) : '-'}</td>
                <td className="px-3 py-2 text-center">
                  {r.journal_entry_id ? (
                    <a href={`/api/v1/pdf/receipt/${r.journal_entry_id}`} target="_blank" rel="noopener noreferrer" title="Download Receipt">
                      <Download className="inline h-3.5 w-3.5 text-gray-400 hover:text-primary-600" />
                    </a>
                  ) : <span className="text-gray-300">-</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
