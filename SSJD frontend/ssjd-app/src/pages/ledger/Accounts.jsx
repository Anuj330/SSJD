import { useState, useMemo } from 'react';
import { Plus, BookOpen, Pencil } from 'lucide-react';
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
  const { data: accountsData, loading, execute: refresh } = useApi(() => ledgerService.listAccounts());
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const debouncedSearch = useDebounce(search);

  const accounts = Array.isArray(accountsData) ? accountsData : [];

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
    { key: 'category', label: 'Category', render: (v) => v || <span className="text-gray-300 dark:text-gray-600">—</span> },
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
    { key: 'is_active', label: 'Status', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'active' : 'inactive'}</Badge> },
    {
      key: 'account_id', label: '', sortable: false,
      render: (_, row) => (
        <Button variant="ghost" size="sm" title="Edit" onClick={(e) => { e.stopPropagation(); setEditing(row); }}>
          <Pencil className="h-3.5 w-3.5 text-gray-500" />
        </Button>
      ),
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

      {editing && (
        <Modal isOpen onClose={() => setEditing(null)} title={`Edit — ${editing.account_name}`}>
          <AccountForm account={editing} onSuccess={() => { setEditing(null); refresh(); }} onCancel={() => setEditing(null)} />
        </Modal>
      )}
    </div>
  );
}

function AccountForm({ account, onSuccess, onCancel }) {
  const isEdit = !!account;
  const [form, setForm] = useState({
    name: account?.account_name || '',
    type: account?.account_type || '',
    category: account?.category || '',
    code: '',
    owner_type: account?.owner_type || 'society',
    owner_id: '',
    is_active: account ? account.is_active : true,
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [advanced, setAdvanced] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const errs = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!form.type) errs.type = 'Type is required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      if (isEdit) {
        await ledgerService.updateAccount(account.account_id, {
          name: form.name.trim(), type: form.type,
          category: form.category.trim(), is_active: !!form.is_active,
        });
        toast.success('Account updated');
      } else {
        const payload = { name: form.name.trim(), type: form.type, owner_type: form.owner_type || 'society' };
        if (form.category.trim()) payload.category = form.category.trim();
        if (form.code.trim()) payload.code = form.code.trim();
        if (form.owner_id) payload.owner_id = Number(form.owner_id);
        await ledgerService.createAccount(payload);
        toast.success('Account created');
      }
      onSuccess?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Account Name" placeholder="e.g. Rent Expense, Grant Income, Petty Cash" value={form.name} onChange={set('name')} error={errors.name} />
      <Select label="Account Type" value={form.type} onChange={set('type')} options={typeOptions} placeholder="Select type" error={errors.type} />
      <Input label="Category / P&L head (optional)" placeholder="e.g. Interest Income, Admin Expenses" value={form.category} onChange={set('category')} />
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Type controls how the account appears in the Trial Balance, P&amp;L and Balance Sheet
        (Income &amp; Expense feed the P&amp;L; Asset/Liability/Equity feed the Balance Sheet).
        {!isEdit && <> A code is generated automatically (e.g. <span className="font-mono">EXPENS-004</span>).</>}
      </p>

      {isEdit ? (
        <Select label="Status" value={form.is_active ? 'true' : 'false'} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.value === 'true' }))}
          options={[{ value: 'true', label: 'Active' }, { value: 'false', label: 'Inactive' }]} />
      ) : (
        <>
          <button type="button" onClick={() => setAdvanced((a) => !a)} className="text-sm font-medium text-primary-600 dark:text-primary-400">
            {advanced ? 'Hide' : 'Advanced options'}
          </button>
          {advanced && (
            <div className="space-y-4 rounded-lg border border-gray-200 p-3 dark:border-gray-800">
              <Input label="Custom code (optional)" placeholder="auto-generated if blank" value={form.code} onChange={set('code')} />
              <Select label="Owner Type" value={form.owner_type} onChange={set('owner_type')} options={ownerTypeOptions} placeholder="Society" />
              <Input label="Owner ID (optional)" type="number" placeholder="Member / Society ID" value={form.owner_id} onChange={set('owner_id')} />
            </div>
          )}
        </>
      )}

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{isEdit ? 'Save Changes' : 'Create Account'}</Button>
      </div>
    </form>
  );
}
