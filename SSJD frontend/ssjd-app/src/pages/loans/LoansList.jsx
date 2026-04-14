import { useState, useMemo } from 'react';
import { Plus, CheckCircle, XCircle, Banknote, CreditCard, Calendar } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import DataTable from '../../components/ui/DataTable';
import EmptyState from '../../components/ui/EmptyState';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import { useApi } from '../../hooks/useApi';
import { useDebounce } from '../../hooks/useDebounce';
import { useRazorpay } from '../../hooks/useRazorpay';
import { useAuthStore } from '../../store/authStore';
import { loansService } from '../../services/loans';
import { membersService } from '../../services/members';
import toast from 'react-hot-toast';

const statusColors = { applied: 'yellow', approved: 'blue', rejected: 'red', disbursed: 'purple', active: 'green', closed: 'gray', defaulted: 'red' };

export default function LoansList() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';
  const { data: loans, loading, execute: refresh } = useApi(() => loansService.list());
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search);
  const [showApply, setShowApply] = useState(false);
  const [actionModal, setActionModal] = useState(null);
  const [scheduleModal, setScheduleModal] = useState(null);
  const [payModal, setPayModal] = useState(null);
  const [payAmount, setPayAmount] = useState('');
  const { pay, loading: paying } = useRazorpay();

  const list = loans ?? [];
  const filtered = useMemo(() => {
    if (!debouncedSearch) return list;
    const q = debouncedSearch.toLowerCase();
    return list.filter(l => l.loan_number.toLowerCase().includes(q) || (l.member_name || '').toLowerCase().includes(q) || (l.product_name || '').toLowerCase().includes(q));
  }, [list, debouncedSearch]);

  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const columns = [
    { key: 'loan_number', label: 'Loan #', render: v => <span className="font-mono text-xs font-medium">{v}</span> },
    { key: 'member_name', label: 'Member' },
    { key: 'product_name', label: 'Product' },
    { key: 'disbursed_amount', label: 'Disbursed', render: v => v > 0 ? fmt(v) : '-' },
    { key: 'outstanding_principal', label: 'Outstanding', render: v => <span className="font-semibold text-amber-600 dark:text-amber-400">{fmt(v)}</span> },
    { key: 'interest_rate', label: 'Rate', render: v => `${Number(v).toFixed(2)}%` },
    { key: 'tenure_months', label: 'Tenure', render: v => `${v}m` },
    { key: 'status', label: 'Status', render: v => <Badge color={statusColors[v] || 'gray'}>{v}</Badge> },
    ...(isAdmin ? [{
      key: 'id', label: 'Actions', sortable: false,
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'applied' && <>
            <Button variant="ghost" size="sm" title="Approve" onClick={e => { e.stopPropagation(); setActionModal({ type: 'approve', loan: row }); }}><CheckCircle className="h-3.5 w-3.5 text-green-500" /></Button>
            <Button variant="ghost" size="sm" title="Reject" onClick={e => { e.stopPropagation(); setActionModal({ type: 'reject', loan: row }); }}><XCircle className="h-3.5 w-3.5 text-red-500" /></Button>
          </>}
          {row.status === 'approved' && <Button variant="ghost" size="sm" title="Disburse" onClick={e => { e.stopPropagation(); setActionModal({ type: 'disburse', loan: row }); }}><Banknote className="h-3.5 w-3.5 text-purple-500" /></Button>}
          {row.status === 'active' && <Button variant="ghost" size="sm" title="Repay" onClick={e => { e.stopPropagation(); setActionModal({ type: 'repay', loan: row }); }}><CreditCard className="h-3.5 w-3.5 text-emerald-500" /></Button>}
          {row.status === 'active' && <Button variant="ghost" size="sm" title="Pay Online" onClick={e => { e.stopPropagation(); setPayModal(row); setPayAmount(''); }}><CreditCard className="h-3.5 w-3.5 text-indigo-500" /></Button>}
          {['active', 'closed'].includes(row.status) && <Button variant="ghost" size="sm" title="Schedule" onClick={e => { e.stopPropagation(); setScheduleModal(row); }}><Calendar className="h-3.5 w-3.5 text-blue-500" /></Button>}
        </div>
      ),
    }] : []),
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Loans</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Manage loan applications, disbursements, and repayments</p>
        </div>
        {isAdmin && <Button onClick={() => setShowApply(true)}><Plus className="h-4 w-4" /> Apply Loan</Button>}
      </div>
      <Card>
        {!loading && list.length === 0
          ? <EmptyState title="No loans" description="Apply for a loan to get started." action={isAdmin && <Button onClick={() => setShowApply(true)}><Plus className="h-4 w-4" /> Apply Loan</Button>} />
          : <DataTable columns={columns} data={filtered} loading={loading} searchable searchValue={search} onSearchChange={setSearch} onRowClick={row => ['active', 'closed'].includes(row.status) && setScheduleModal(row)} />}
      </Card>

      <Modal isOpen={showApply} onClose={() => setShowApply(false)} title="Apply for Loan" size="lg">
        <LoanApplyForm onSuccess={() => { setShowApply(false); refresh(); }} onCancel={() => setShowApply(false)} />
      </Modal>

      {actionModal && <Modal isOpen onClose={() => setActionModal(null)} title={`${actionModal.type.charAt(0).toUpperCase() + actionModal.type.slice(1)} — ${actionModal.loan.loan_number}`}>
        <LoanActionForm {...actionModal} onSuccess={() => { setActionModal(null); refresh(); }} onCancel={() => setActionModal(null)} />
      </Modal>}

      {scheduleModal && <Modal isOpen onClose={() => setScheduleModal(null)} title={`EMI Schedule — ${scheduleModal.loan_number}`} size="xl">
        <LoanSchedule loanId={scheduleModal.id} />
      </Modal>}

      {payModal && (
        <Modal isOpen onClose={() => setPayModal(null)} title={`Pay Online — ${payModal.loan_number}`} size="sm">
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Member: <strong>{payModal.member_name}</strong> | Outstanding: <strong className="text-amber-600">{fmt(payModal.outstanding_principal)}</strong>
            </p>
            <Input label="Payment Amount (INR)" type="number" min="1" placeholder="Enter EMI amount" value={payAmount} onChange={e => setPayAmount(e.target.value)} />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setPayModal(null)}>Cancel</Button>
              <Button loading={paying} disabled={!payAmount || Number(payAmount) <= 0} onClick={() => {
                const amt = Number(payAmount);
                if (amt > 0) pay('loan_repayment', payModal.id, amt, () => { setPayModal(null); setPayAmount(''); refresh(); });
              }}>
                <CreditCard className="h-4 w-4" /> Pay {payAmount ? fmt(Number(payAmount)) : ''}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

function LoanApplyForm({ onSuccess, onCancel }) {
  const { data: products } = useApi(() => loansService.listProducts());
  const { data: members } = useApi(() => membersService.list());
  const [form, setForm] = useState({ member_id: '', product_id: '', amount: '', tenure_months: '', remarks: '' });
  const [loading, setLoading] = useState(false);
  const set = f => e => setForm(p => ({ ...p, [f]: e.target.value }));
  const memberList = Array.isArray(members) ? members : members?.members ?? [];
  const prodList = (products ?? []).filter(p => p.is_active);

  const handleSubmit = async e => {
    e.preventDefault();
    if (!form.member_id || !form.product_id || !form.amount || !form.tenure_months) { toast.error('Fill all required fields'); return; }
    setLoading(true);
    try {
      await loansService.apply({ member_id: Number(form.member_id), product_id: Number(form.product_id), amount: Number(form.amount), tenure_months: Number(form.tenure_months), remarks: form.remarks || undefined });
      toast.success('Loan application submitted');
      onSuccess?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Select label="Member" value={form.member_id} onChange={set('member_id')} options={memberList.map(m => ({ value: String(m.id), label: `${m.name} (#${m.id})` }))} placeholder="Select" />
      <Select label="Product" value={form.product_id} onChange={set('product_id')} options={prodList.map(p => ({ value: String(p.id), label: `${p.name} (${p.interest_rate}%)` }))} placeholder="Select" />
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Amount" type="number" min="1" value={form.amount} onChange={set('amount')} />
        <Input label="Tenure (months)" type="number" min="1" value={form.tenure_months} onChange={set('tenure_months')} />
      </div>
      <Input label="Remarks" value={form.remarks} onChange={set('remarks')} />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>Submit Application</Button>
      </div>
    </form>
  );
}

function LoanActionForm({ type, loan, onSuccess, onCancel }) {
  const [amount, setAmount] = useState(type === 'approve' ? loan.applied_amount : '');
  const [remarks, setRemarks] = useState('');
  const [loading, setLoading] = useState(false);
  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      if (type === 'approve') { await loansService.approve(loan.id, { sanctioned_amount: Number(amount), remarks }); toast.success('Loan approved'); }
      else if (type === 'reject') { await loansService.reject(loan.id, remarks || 'Rejected'); toast.success('Loan rejected'); }
      else if (type === 'disburse') { await loansService.disburse(loan.id); toast.success('Loan disbursed'); }
      else if (type === 'repay') { const res = await loansService.repay(loan.id, { amount: Number(amount) }); toast.success(`Repayment of ${fmt(res.amount_applied)} recorded`); }
      onSuccess?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  if (type === 'disburse') return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600 dark:text-gray-400">Disburse <strong>{fmt(loan.sanctioned_amount || loan.applied_amount)}</strong> for loan {loan.loan_number}?</p>
      <div className="flex justify-end gap-3"><Button variant="secondary" onClick={onCancel}>Cancel</Button><Button loading={loading} onClick={handleSubmit}>Disburse</Button></div>
    </div>
  );

  if (type === 'reject') return (
    <div className="space-y-4">
      <Input label="Reason" value={remarks} onChange={e => setRemarks(e.target.value)} />
      <div className="flex justify-end gap-3"><Button variant="secondary" onClick={onCancel}>Cancel</Button><Button variant="danger" loading={loading} onClick={handleSubmit}>Reject</Button></div>
    </div>
  );

  return (
    <div className="space-y-4">
      {type === 'approve' && <p className="text-sm text-gray-600 dark:text-gray-400">Applied: {fmt(loan.applied_amount)}</p>}
      {type === 'repay' && <p className="text-sm text-gray-600 dark:text-gray-400">Outstanding: <strong className="text-amber-600">{fmt(loan.outstanding_principal)}</strong></p>}
      <Input label={type === 'approve' ? 'Sanctioned Amount' : 'Repayment Amount'} type="number" min="1" value={amount} onChange={e => setAmount(e.target.value)} />
      {type === 'approve' && <Input label="Remarks" value={remarks} onChange={e => setRemarks(e.target.value)} />}
      <div className="flex justify-end gap-3"><Button variant="secondary" onClick={onCancel}>Cancel</Button><Button loading={loading} onClick={handleSubmit}>{type === 'approve' ? 'Approve' : 'Record Payment'}</Button></div>
    </div>
  );
}

function LoanSchedule({ loanId }) {
  const { data, loading } = useApi(() => loansService.getSchedule(loanId));
  const fmt = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  if (loading) return <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />)}</div>;

  const rows = data?.schedule ?? [];
  if (!rows.length) return <p className="py-4 text-center text-sm text-gray-500">No schedule generated yet.</p>;

  return (
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
  );
}
