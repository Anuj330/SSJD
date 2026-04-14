import { useState, useMemo } from 'react';
import { Plus, Edit2 } from 'lucide-react';
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
import { loansService } from '../../services/loans';
import toast from 'react-hot-toast';

const typeOptions = [
  { value: 'personal', label: 'Personal' }, { value: 'emergency', label: 'Emergency' },
  { value: 'gold', label: 'Gold' }, { value: 'property', label: 'Property' },
  { value: 'agriculture', label: 'Agriculture' }, { value: 'education', label: 'Education' },
];
const freqOptions = [
  { value: 'monthly', label: 'Monthly' }, { value: 'quarterly', label: 'Quarterly' },
  { value: 'half_yearly', label: 'Half Yearly' }, { value: 'yearly', label: 'Yearly' },
  { value: 'bullet', label: 'Bullet (Lump Sum)' },
];
const typeColors = { personal: 'blue', emergency: 'red', gold: 'yellow', property: 'purple', agriculture: 'green', education: 'blue' };

export default function LoanProducts() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';
  const { data: products, loading, execute: refresh } = useApi(() => loansService.listProducts());
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editProd, setEditProd] = useState(null);
  const debouncedSearch = useDebounce(search);
  const list = products ?? [];

  const filtered = useMemo(() => {
    if (!debouncedSearch) return list;
    const q = debouncedSearch.toLowerCase();
    return list.filter(p => p.name.toLowerCase().includes(q) || p.loan_type.toLowerCase().includes(q));
  }, [list, debouncedSearch]);

  const fmt = n => n != null ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n) : '-';

  const columns = [
    { key: 'name', label: 'Product Name', render: v => <span className="font-medium">{v}</span> },
    { key: 'loan_type', label: 'Type', render: v => <Badge color={typeColors[v] || 'gray'}>{v}</Badge> },
    { key: 'interest_rate', label: 'Rate', render: v => <span className="font-semibold text-emerald-600 dark:text-emerald-400">{Number(v).toFixed(2)}%</span> },
    { key: 'max_tenure_months', label: 'Max Tenure', render: v => `${v} months` },
    { key: 'min_amount', label: 'Min', render: v => fmt(v) },
    { key: 'max_amount', label: 'Max', render: v => fmt(v) },
    { key: 'is_active', label: 'Status', render: v => <Badge color={v ? 'green' : 'red'}>{v ? 'Active' : 'Inactive'}</Badge> },
    ...(isAdmin ? [{ key: 'id', label: '', sortable: false, render: (_, row) => (
      <Button variant="ghost" size="sm" onClick={e => { e.stopPropagation(); setEditProd(row); setShowForm(true); }}><Edit2 className="h-3.5 w-3.5" /></Button>
    )}] : []),
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Loan Products</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Loan scheme configurations</p>
        </div>
        {isAdmin && <Button onClick={() => { setEditProd(null); setShowForm(true); }}><Plus className="h-4 w-4" /> New Product</Button>}
      </div>
      <Card>
        {!loading && list.length === 0
          ? <EmptyState title="No loan products" description="Create your first loan product." action={isAdmin && <Button onClick={() => setShowForm(true)}><Plus className="h-4 w-4" /> New Product</Button>} />
          : <DataTable columns={columns} data={filtered} loading={loading} searchable searchValue={search} onSearchChange={setSearch} />}
      </Card>
      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title={editProd ? 'Edit Product' : 'Create Product'} size="lg">
        <LoanProductForm product={editProd} onSuccess={() => { setShowForm(false); setEditProd(null); refresh(); }} onCancel={() => { setShowForm(false); setEditProd(null); }} />
      </Modal>
    </div>
  );
}

function LoanProductForm({ product, onSuccess, onCancel }) {
  const [form, setForm] = useState({
    name: product?.name || '', loan_type: product?.loan_type || '', description: product?.description || '',
    interest_rate: product?.interest_rate?.toString() || '', min_amount: product?.min_amount?.toString() || '0',
    max_amount: product?.max_amount?.toString() || '', max_tenure_months: product?.max_tenure_months?.toString() || '60',
    repayment_freq: product?.repayment_freq || 'monthly', late_penalty_pct: product?.late_penalty_pct?.toString() || '0',
    processing_fee_pct: product?.processing_fee_pct?.toString() || '0', is_active: product?.is_active ?? true,
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const set = f => e => setForm(p => ({ ...p, [f]: e.target.value }));

  const handleSubmit = async e => {
    e.preventDefault();
    const errs = {};
    if (!form.name.trim()) errs.name = 'Required';
    if (!product && !form.loan_type) errs.loan_type = 'Required';
    if (!form.interest_rate) errs.interest_rate = 'Required';
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setLoading(true);
    try {
      const payload = {
        name: form.name, description: form.description || null, interest_rate: Number(form.interest_rate),
        min_amount: Number(form.min_amount || 0), max_amount: form.max_amount ? Number(form.max_amount) : null,
        max_tenure_months: Number(form.max_tenure_months || 60), repayment_freq: form.repayment_freq,
        late_penalty_pct: Number(form.late_penalty_pct || 0), processing_fee_pct: Number(form.processing_fee_pct || 0),
      };
      if (product) { payload.is_active = form.is_active; await loansService.updateProduct(product.id, payload); toast.success('Updated'); }
      else { payload.loan_type = form.loan_type; await loansService.createProduct(payload); toast.success('Created'); }
      onSuccess?.();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Product Name" value={form.name} onChange={set('name')} error={errors.name} />
        {!product && <Select label="Loan Type" value={form.loan_type} onChange={set('loan_type')} options={typeOptions} placeholder="Select" error={errors.loan_type} />}
        <Input label="Interest Rate (%)" type="number" step="0.01" value={form.interest_rate} onChange={set('interest_rate')} error={errors.interest_rate} />
        <Select label="Repayment Frequency" value={form.repayment_freq} onChange={set('repayment_freq')} options={freqOptions} />
        <Input label="Min Amount" type="number" value={form.min_amount} onChange={set('min_amount')} />
        <Input label="Max Amount" type="number" value={form.max_amount} onChange={set('max_amount')} placeholder="No limit" />
        <Input label="Max Tenure (months)" type="number" value={form.max_tenure_months} onChange={set('max_tenure_months')} />
        <Input label="Late Penalty (%)" type="number" step="0.01" value={form.late_penalty_pct} onChange={set('late_penalty_pct')} />
        <Input label="Processing Fee (%)" type="number" step="0.01" value={form.processing_fee_pct} onChange={set('processing_fee_pct')} />
      </div>
      <Input label="Description" value={form.description} onChange={set('description')} />
      {product && <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={e => setForm(p => ({ ...p, is_active: e.target.checked }))} className="h-4 w-4 rounded border-gray-300 text-primary-600" /> Active</label>}
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{product ? 'Update' : 'Create'}</Button>
      </div>
    </form>
  );
}
