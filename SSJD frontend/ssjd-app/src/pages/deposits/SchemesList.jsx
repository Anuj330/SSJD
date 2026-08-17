import { useState, useMemo } from 'react';
import { Plus, BookOpen, Edit2 } from 'lucide-react';
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
import { useAuthStore } from '../../store/authStore';
import { schemesService } from '../../services/schemes';
import toast from 'react-hot-toast';

const typeColors = { fd: 'blue', rd: 'purple', mis: 'yellow', savings: 'green' };
const typeLabels = { fd: 'Fixed Deposit', rd: 'Recurring Deposit', mis: 'MIS', savings: 'Savings' };

const typeOptions = [
  { value: 'fd', label: 'Fixed Deposit' },
  { value: 'rd', label: 'Recurring Deposit' },
  { value: 'mis', label: 'Monthly Income Scheme' },
  { value: 'savings', label: 'Savings' },
];

const compoundingOptions = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'half_yearly', label: 'Half Yearly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'on_maturity', label: 'On Maturity' },
];

export default function SchemesList() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';
  const { data: schemes, loading, execute: refresh } = useApi(() => schemesService.list());
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editScheme, setEditScheme] = useState(null);
  const debouncedSearch = useDebounce(search);

  const list = schemes ?? [];

  const filtered = useMemo(() => {
    if (!debouncedSearch) return list;
    const q = debouncedSearch.toLowerCase();
    return list.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.scheme_type.toLowerCase().includes(q)
    );
  }, [list, debouncedSearch]);

  const fmt = (n) =>
    n != null
      ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n)
      : '-';

  const columns = [
    { key: 'name', label: 'Scheme Name', render: (v) => <span className="font-medium">{v}</span> },
    {
      key: 'scheme_type',
      label: 'Type',
      render: (v) => <Badge color={typeColors[v] || 'gray'}>{typeLabels[v] || v}</Badge>,
    },
    {
      key: 'interest_rate',
      label: 'Interest Rate',
      render: (v) => <span className="font-semibold text-emerald-600 dark:text-emerald-400">{Number(v).toFixed(2)}%</span>,
    },
    { key: 'min_amount', label: 'Min Amount', render: (v) => fmt(v) },
    { key: 'max_amount', label: 'Max Amount', render: (v) => fmt(v) },
    {
      key: 'tenure_months',
      label: 'Tenure',
      render: (v) => (v ? `${v} months` : 'Open-ended'),
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (v) => <Badge color={v ? 'green' : 'red'}>{v ? 'Active' : 'Inactive'}</Badge>,
    },
    ...(isAdmin
      ? [
          {
            key: 'id',
            label: '',
            sortable: false,
            render: (_, row) => (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setEditScheme(row);
                  setShowForm(true);
                }}
              >
                <Edit2 className="h-3.5 w-3.5" />
              </Button>
            ),
          },
        ]
      : []),
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Deposit Schemes</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            FD, RD, MIS, and Savings scheme configurations
          </p>
        </div>
        {isAdmin && (
          <Button
            onClick={() => {
              setEditScheme(null);
              setShowForm(true);
            }}
          >
            <Plus className="h-4 w-4" /> New Scheme
          </Button>
        )}
      </div>

      <Card>
        {!loading && list.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No schemes yet"
            description="Create your first deposit scheme to start accepting deposits."
            action={
              isAdmin && (
                <Button onClick={() => setShowForm(true)}>
                  <Plus className="h-4 w-4" /> New Scheme
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
            emptyMessage="No matching schemes"
          />
        )}
      </Card>

      <Modal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title={editScheme ? 'Edit Scheme' : 'Create Scheme'}
        size="lg"
      >
        <SchemeForm
          scheme={editScheme}
          onSuccess={() => {
            setShowForm(false);
            setEditScheme(null);
            refresh();
          }}
          onCancel={() => {
            setShowForm(false);
            setEditScheme(null);
          }}
        />
      </Modal>
    </div>
  );
}

function SchemeForm({ scheme, onSuccess, onCancel }) {
  const [form, setForm] = useState({
    name: scheme?.name || '',
    scheme_type: scheme?.scheme_type || '',
    description: scheme?.description || '',
    interest_rate: scheme?.interest_rate?.toString() || '',
    min_amount: scheme?.min_amount?.toString() || '0',
    max_amount: scheme?.max_amount?.toString() || '',
    tenure_months: scheme?.tenure_months?.toString() || '',
    compounding: scheme?.compounding || 'quarterly',
    premature_penalty_pct: scheme?.premature_penalty_pct?.toString() || '0',
    is_active: scheme?.is_active ?? true,
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const errs = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!scheme && !form.scheme_type) errs.scheme_type = 'Type is required';
    if (!form.interest_rate || Number(form.interest_rate) < 0) errs.interest_rate = 'Valid interest rate required';
    if (!form.compounding) errs.compounding = 'Compounding is required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const payload = {
        name: form.name,
        description: form.description || null,
        interest_rate: Number(form.interest_rate),
        min_amount: Number(form.min_amount || 0),
        max_amount: form.max_amount ? Number(form.max_amount) : null,
        tenure_months: form.tenure_months ? Number(form.tenure_months) : null,
        compounding: form.compounding,
        premature_penalty_pct: Number(form.premature_penalty_pct || 0),
      };

      if (scheme) {
        payload.is_active = form.is_active;
        await schemesService.update(scheme.id, payload);
        toast.success('Scheme updated');
      } else {
        payload.scheme_type = form.scheme_type;
        await schemesService.create(payload);
        toast.success('Scheme created');
      }
      onSuccess?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save scheme');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Scheme Name" placeholder="e.g. Fixed Deposit 1 Year" value={form.name} onChange={set('name')} error={errors.name} />
        {!scheme && (
          <Select label="Scheme Type" value={form.scheme_type} onChange={set('scheme_type')} options={typeOptions} placeholder="Select type" error={errors.scheme_type} />
        )}
        <Input label="Interest Rate (%)" type="number" step="0.01" min="0" placeholder="e.g. 7.50" value={form.interest_rate} onChange={set('interest_rate')} error={errors.interest_rate} />
        <Select label="Compounding" value={form.compounding} onChange={set('compounding')} options={compoundingOptions} error={errors.compounding} />
        <Input label="Min Amount" type="number" min="0" value={form.min_amount} onChange={set('min_amount')} />
        <Input label="Max Amount (optional)" type="number" min="0" placeholder="No limit" value={form.max_amount} onChange={set('max_amount')} />
        <Input label="Tenure (months, optional)" type="number" min="1" placeholder="Open-ended" value={form.tenure_months} onChange={set('tenure_months')} />
        <Input label="Premature Penalty (%)" type="number" step="0.01" min="0" value={form.premature_penalty_pct} onChange={set('premature_penalty_pct')} />
      </div>
      <div>
        <Input label="Description (optional)" placeholder="Brief description" value={form.description} onChange={set('description')} />
      </div>
      {scheme && (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_active"
            checked={form.is_active}
            onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <label htmlFor="is_active" className="text-sm text-gray-700 dark:text-gray-300">Active</label>
        </div>
      )}
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{scheme ? 'Update' : 'Create'} Scheme</Button>
      </div>
    </form>
  );
}
