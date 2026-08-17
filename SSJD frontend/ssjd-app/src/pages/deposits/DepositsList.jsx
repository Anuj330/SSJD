import { useState, useMemo } from 'react';
import { Plus, Wallet, ArrowDownCircle, ArrowUpCircle, XCircle, Calculator, FileText, CreditCard } from 'lucide-react';
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
import { depositsService } from '../../services/deposits';
import { schemesService } from '../../services/schemes';
import { membersService } from '../../services/members';
import toast from 'react-hot-toast';

const statusColors = {
  active: 'green',
  matured: 'blue',
  closed: 'gray',
  premature_closed: 'red',
};

const statusLabels = {
  active: 'Active',
  matured: 'Matured',
  closed: 'Closed',
  premature_closed: 'Pre-closed',
};

export default function DepositsList() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';
  const { data: deposits, loading, execute: refresh } = useApi(() => depositsService.list());
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search);

  const [showOpen, setShowOpen] = useState(false);
  const [actionModal, setActionModal] = useState(null); // { type, deposit }
  const [statementModal, setStatementModal] = useState(null);
  const [payModal, setPayModal] = useState(null);
  const [payAmount, setPayAmount] = useState('');
  const { pay, loading: paying } = useRazorpay();

  const list = deposits ?? [];

  const filtered = useMemo(() => {
    if (!debouncedSearch) return list;
    const q = debouncedSearch.toLowerCase();
    return list.filter(
      (d) =>
        d.account_number.toLowerCase().includes(q) ||
        (d.member_name || '').toLowerCase().includes(q) ||
        (d.scheme_name || '').toLowerCase().includes(q)
    );
  }, [list, debouncedSearch]);

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const columns = [
    {
      key: 'account_number',
      label: 'Account #',
      render: (v) => <span className="font-mono text-xs font-medium">{v}</span>,
    },
    { key: 'member_name', label: 'Member' },
    { key: 'scheme_name', label: 'Scheme' },
    {
      key: 'current_balance',
      label: 'Balance',
      render: (v) => <span className="font-semibold text-emerald-600 dark:text-emerald-400">{fmt(v)}</span>,
    },
    {
      key: 'interest_earned',
      label: 'Interest',
      render: (v) => <span className="text-blue-600 dark:text-blue-400">{fmt(v)}</span>,
    },
    { key: 'opened_date', label: 'Opened' },
    {
      key: 'maturity_date',
      label: 'Maturity',
      render: (v) => v || '-',
    },
    {
      key: 'status',
      label: 'Status',
      render: (v) => <Badge color={statusColors[v] || 'gray'}>{statusLabels[v] || v}</Badge>,
    },
    ...(isAdmin
      ? [
          {
            key: 'id',
            label: 'Actions',
            sortable: false,
            render: (_, row) =>
              row.status === 'active' ? (
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    title="Deposit"
                    onClick={(e) => { e.stopPropagation(); setActionModal({ type: 'deposit', deposit: row }); }}
                  >
                    <ArrowDownCircle className="h-3.5 w-3.5 text-emerald-500" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    title="Withdraw"
                    onClick={(e) => { e.stopPropagation(); setActionModal({ type: 'withdraw', deposit: row }); }}
                  >
                    <ArrowUpCircle className="h-3.5 w-3.5 text-amber-500" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    title="Pay Online"
                    onClick={(e) => { e.stopPropagation(); setPayModal(row); setPayAmount(''); }}
                  >
                    <CreditCard className="h-3.5 w-3.5 text-indigo-500" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    title="Interest"
                    onClick={(e) => { e.stopPropagation(); setActionModal({ type: 'interest', deposit: row }); }}
                  >
                    <Calculator className="h-3.5 w-3.5 text-blue-500" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    title="Close"
                    onClick={(e) => { e.stopPropagation(); setActionModal({ type: 'close', deposit: row }); }}
                  >
                    <XCircle className="h-3.5 w-3.5 text-red-500" />
                  </Button>
                </div>
              ) : null,
          },
        ]
      : []),
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Deposit Accounts</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage member deposit accounts — FD, RD, MIS, Savings
          </p>
        </div>
        <div className="flex gap-2">
          {isAdmin && (
            <Button onClick={() => setShowOpen(true)}>
              <Plus className="h-4 w-4" /> Open Deposit
            </Button>
          )}
        </div>
      </div>

      <Card>
        {!loading && list.length === 0 ? (
          <EmptyState
            icon={Wallet}
            title="No deposits yet"
            description="Open a deposit account for a member to get started."
            action={
              isAdmin && (
                <Button onClick={() => setShowOpen(true)}>
                  <Plus className="h-4 w-4" /> Open Deposit
                </Button>
              )
            }
          />
        ) : (
          <DataTable
            columns={columns}
            data={filtered}
            loading={loading}
            searchable
            searchValue={search}
            onSearchChange={setSearch}
            emptyMessage="No matching deposits"
            onRowClick={(row) => setStatementModal(row)}
          />
        )}
      </Card>

      {/* Open Deposit Modal */}
      <Modal isOpen={showOpen} onClose={() => setShowOpen(false)} title="Open Deposit Account" size="lg">
        <OpenDepositForm
          onSuccess={() => { setShowOpen(false); refresh(); }}
          onCancel={() => setShowOpen(false)}
        />
      </Modal>

      {/* Deposit / Withdraw / Interest / Close Modal */}
      {actionModal && (
        <Modal
          isOpen
          onClose={() => setActionModal(null)}
          title={
            actionModal.type === 'deposit'
              ? `Deposit to ${actionModal.deposit.account_number}`
              : actionModal.type === 'withdraw'
              ? `Withdraw from ${actionModal.deposit.account_number}`
              : actionModal.type === 'interest'
              ? `Calculate Interest — ${actionModal.deposit.account_number}`
              : `Close ${actionModal.deposit.account_number}`
          }
        >
          <DepositActionForm
            type={actionModal.type}
            deposit={actionModal.deposit}
            onSuccess={() => { setActionModal(null); refresh(); }}
            onCancel={() => setActionModal(null)}
          />
        </Modal>
      )}

      {/* Statement Modal */}
      {statementModal && (
        <Modal isOpen onClose={() => setStatementModal(null)} title={`Statement — ${statementModal.account_number}`} size="xl">
          <DepositStatement deposit={statementModal} />
        </Modal>
      )}

      {/* Pay Online Modal */}
      {payModal && (
        <Modal isOpen onClose={() => setPayModal(null)} title={`Pay Online — ${payModal.account_number}`} size="sm">
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Member: <strong>{payModal.member_name}</strong> | Balance: <strong className="text-emerald-600">{fmt(payModal.current_balance)}</strong>
            </p>
            <Input label="Amount (INR)" type="number" min="1" placeholder="Enter amount" value={payAmount} onChange={e => setPayAmount(e.target.value)} />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setPayModal(null)}>Cancel</Button>
              <Button loading={paying} disabled={!payAmount || Number(payAmount) <= 0} onClick={() => {
                const amt = Number(payAmount);
                if (amt > 0) pay('deposit', payModal.id, amt, () => { setPayModal(null); setPayAmount(''); refresh(); });
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

// ─── Open Deposit Form ───

function OpenDepositForm({ onSuccess, onCancel }) {
  const { data: schemes } = useApi(() => schemesService.list());
  const { data: members } = useApi(() => membersService.list());
  const [form, setForm] = useState({ member_id: '', scheme_id: '', amount: '' });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const memberList = Array.isArray(members) ? members : members?.members ?? members?.items ?? [];
  const schemeList = (schemes ?? []).filter((s) => s.is_active);

  const memberOptions = memberList.map((m) => ({ value: String(m.id), label: `${m.name} (#${m.id})` }));
  const schemeOptions = schemeList.map((s) => ({ value: String(s.id), label: `${s.name} (${s.interest_rate}%)` }));

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const errs = {};
    if (!form.member_id) errs.member_id = 'Member is required';
    if (!form.scheme_id) errs.scheme_id = 'Scheme is required';
    if (!form.amount || Number(form.amount) <= 0) errs.amount = 'Valid amount required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await depositsService.open({
        member_id: Number(form.member_id),
        scheme_id: Number(form.scheme_id),
        amount: Number(form.amount),
      });
      toast.success('Deposit account opened');
      onSuccess?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to open deposit');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Select label="Member" value={form.member_id} onChange={set('member_id')} options={memberOptions} placeholder="Select member" error={errors.member_id} />
      <Select label="Scheme" value={form.scheme_id} onChange={set('scheme_id')} options={schemeOptions} placeholder="Select scheme" error={errors.scheme_id} />
      <Input label="Initial Deposit Amount" type="number" min="1" placeholder="e.g. 50000" value={form.amount} onChange={set('amount')} error={errors.amount} />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>Open Deposit</Button>
      </div>
    </form>
  );
}

// ─── Deposit / Withdraw / Interest / Close Form ───

function DepositActionForm({ type, deposit, onSuccess, onCancel }) {
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [asOf, setAsOf] = useState('');
  const [loading, setLoading] = useState(false);

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (type === 'deposit') {
        if (!amount || Number(amount) <= 0) {
          toast.error('Enter a valid amount');
          setLoading(false);
          return;
        }
        const res = await depositsService.deposit(deposit.id, {
          amount: Number(amount),
          description: description || undefined,
        });
        toast.success(`Deposited! New balance: ${fmt(res.new_balance)}`);
      } else if (type === 'withdraw') {
        if (!amount || Number(amount) <= 0) {
          toast.error('Enter a valid amount');
          setLoading(false);
          return;
        }
        const res = await depositsService.withdraw(deposit.id, {
          amount: Number(amount),
          description: description || undefined,
        });
        toast.success(`Withdrawn! New balance: ${fmt(res.new_balance)}`);
      } else if (type === 'interest') {
        const res = await depositsService.calculateInterest(deposit.id, asOf || undefined);
        toast.success(`Interest of ${fmt(res.interest_amount)} credited for ${res.days} days`);
      } else if (type === 'close') {
        const res = await depositsService.close(deposit.id);
        toast.success(`Account closed. Payout: ${fmt(res.payout)}${Number(res.penalty) > 0 ? ` (Penalty: ${fmt(res.penalty)})` : ''}`);
      }
      onSuccess?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || `Failed to ${type}`);
    } finally {
      setLoading(false);
    }
  };

  if (type === 'close') {
    return (
      <div className="space-y-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Are you sure you want to close deposit account <strong>{deposit.account_number}</strong>?
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Current balance: <strong className="text-emerald-600">{fmt(deposit.current_balance)}</strong>
        </p>
        {deposit.maturity_date && new Date() < new Date(deposit.maturity_date) && (
          <p className="text-sm text-amber-600 dark:text-amber-400">
            This is a premature closure. A penalty may apply.
          </p>
        )}
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={onCancel}>Cancel</Button>
          <Button variant="danger" loading={loading} onClick={handleSubmit}>Close Account</Button>
        </div>
      </div>
    );
  }

  if (type === 'interest') {
    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Calculate and post accrued interest for <strong>{deposit.account_number}</strong>.
          Current balance: <strong className="text-emerald-600">{fmt(deposit.current_balance)}</strong>
        </p>
        <Input
          label="Calculate As Of (optional, defaults to today)"
          type="date"
          value={asOf}
          onChange={(e) => setAsOf(e.target.value)}
        />
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
          <Button type="submit" loading={loading}>Calculate Interest</Button>
        </div>
      </form>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Current balance: <strong className="text-emerald-600">{fmt(deposit.current_balance)}</strong>
      </p>
      <Input
        label="Amount"
        type="number"
        min="1"
        placeholder="Enter amount"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
      />
      <Input
        label="Description (optional)"
        placeholder="e.g. Monthly deposit"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading} variant={type === 'withdraw' ? 'danger' : 'primary'}>
          {type === 'deposit' ? 'Deposit' : 'Withdraw'}
        </Button>
      </div>
    </form>
  );
}

// ─── Deposit Statement ───

function DepositStatement({ deposit }) {
  const { data: statement, loading } = useApi(() => depositsService.getStatement(deposit.id));

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-5 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        ))}
      </div>
    );
  }

  const rows = statement?.rows ?? [];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50">
          <p className="text-xs text-gray-500">Balance</p>
          <p className="text-lg font-bold text-emerald-600">{fmt(statement?.current_balance ?? 0)}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50">
          <p className="text-xs text-gray-500">Total Credits</p>
          <p className="text-lg font-bold text-emerald-600">{fmt(statement?.total_credit ?? 0)}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50">
          <p className="text-xs text-gray-500">Total Debits</p>
          <p className="text-lg font-bold text-amber-600">{fmt(statement?.total_debit ?? 0)}</p>
        </div>
      </div>

      {rows.length === 0 ? (
        <p className="py-4 text-center text-sm text-gray-500">No transactions yet.</p>
      ) : (
        <div className="max-h-80 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
              <tr>
                <th className="px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Date</th>
                <th className="px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Type</th>
                <th className="px-3 py-2 font-medium text-gray-600 dark:text-gray-400">Ref</th>
                <th className="px-3 py-2 text-right font-medium text-gray-600 dark:text-gray-400">Debit</th>
                <th className="px-3 py-2 text-right font-medium text-gray-600 dark:text-gray-400">Credit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {rows.map((row, i) => (
                <tr key={i} className="bg-white dark:bg-gray-900">
                  <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
                    {new Date(row.created_at).toLocaleDateString('en-IN')}
                  </td>
                  <td className="px-3 py-2">
                    <Badge color={row.txn_type.includes('interest') ? 'blue' : row.txn_type.includes('withdraw') || row.txn_type.includes('close') ? 'red' : 'green'}>
                      {row.txn_type}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-gray-500">{row.txn_ref}</td>
                  <td className="px-3 py-2 text-right text-amber-600 dark:text-amber-400">
                    {Number(row.dr_amount) > 0 ? fmt(row.dr_amount) : ''}
                  </td>
                  <td className="px-3 py-2 text-right text-emerald-600 dark:text-emerald-400">
                    {Number(row.cr_amount) > 0 ? fmt(row.cr_amount) : ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
