import { useState, useMemo } from 'react';
import { Plus, BookOpen } from 'lucide-react';
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
import { ledgerService } from '../../services/ledger';
import toast from 'react-hot-toast';

const typeColors = {
  asset: 'blue',
  liability: 'red',
  income: 'green',
  expense: 'yellow',
  equity: 'purple',
};

const typeOptions = [
  { value: 'asset', label: 'Asset' },
  { value: 'liability', label: 'Liability' },
  { value: 'income', label: 'Income' },
  { value: 'expense', label: 'Expense' },
  { value: 'equity', label: 'Equity' },
];

const ownerTypeOptions = [
  { value: 'society', label: 'Society' },
  { value: 'member', label: 'Member' },
  { value: 'system', label: 'System' },
];

export default function Accounts() {
  const { data: trialBalance, loading, execute: refresh } = useApi(() => ledgerService.getTrialBalance());
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const debouncedSearch = useDebounce(search);

  const accounts = trialBalance?.rows ?? [];

  const filtered = useMemo(() => {
    if (!debouncedSearch) return accounts;
    const q = debouncedSearch.toLowerCase();
    return accounts.filter(
      (a) => a.account_name.toLowerCase().includes(q) || a.account_code.toLowerCase().includes(q) || a.account_type.toLowerCase().includes(q)
    );
  }, [accounts, debouncedSearch]);

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const columns = [
    { key: 'account_code', label: 'Code', render: (v) => <span className="font-mono text-xs">{v}</span> },
    { key: 'account_name', label: 'Name', render: (v) => <span className="font-medium">{v}</span> },
    {
      key: 'account_type',
      label: 'Type',
      render: (v) => <Badge color={typeColors[v] || 'gray'}>{v}</Badge>,
    },
    {
      key: 'total_debit',
      label: 'Total Debit',
      render: (v) => <span className="text-amber-600 dark:text-amber-400">{fmt(v)}</span>,
    },
    {
      key: 'total_credit',
      label: 'Total Credit',
      render: (v) => <span className="text-emerald-600 dark:text-emerald-400">{fmt(v)}</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Ledger Accounts</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Chart of accounts for double-entry bookkeeping
          </p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4" /> New Account
        </Button>
      </div>

      <Card>
        {!loading && accounts.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No accounts yet"
            description="Create your first ledger account to start tracking finances."
            action={
              <Button onClick={() => setShowForm(true)}>
                <Plus className="h-4 w-4" /> New Account
              </Button>
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
          />
        )}
      </Card>

      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title="Create Account">
        <AccountForm onSuccess={() => { setShowForm(false); refresh(); }} onCancel={() => setShowForm(false)} />
      </Modal>
    </div>
  );
}

function AccountForm({ onSuccess, onCancel }) {
  const [form, setForm] = useState({ code: '', name: '', type: '', owner_type: '', owner_id: '' });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const errs = {};
    if (!form.code.trim()) errs.code = 'Code is required';
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!form.type) errs.type = 'Type is required';
    if (!form.owner_type) errs.owner_type = 'Owner type is required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const payload = { code: form.code, name: form.name, type: form.type, owner_type: form.owner_type };
      if (form.owner_id) payload.owner_id = Number(form.owner_id);
      await ledgerService.createAccount(payload);
      toast.success('Account created');
      onSuccess?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Account Code" placeholder="e.g. CASH-001" value={form.code} onChange={set('code')} error={errors.code} />
      <Input label="Account Name" placeholder="e.g. Cash in Hand" value={form.name} onChange={set('name')} error={errors.name} />
      <Select label="Account Type" value={form.type} onChange={set('type')} options={typeOptions} placeholder="Select type" error={errors.type} />
      <Select label="Owner Type" value={form.owner_type} onChange={set('owner_type')} options={ownerTypeOptions} placeholder="Select owner type" error={errors.owner_type} />
      <Input label="Owner ID (optional)" type="number" placeholder="Member or Society ID" value={form.owner_id} onChange={set('owner_id')} />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>Create Account</Button>
      </div>
    </form>
  );
}
