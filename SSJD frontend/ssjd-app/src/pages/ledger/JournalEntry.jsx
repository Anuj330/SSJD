import { useState } from 'react';
import { Plus, Trash2, FileText } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Badge from '../../components/ui/Badge';
import { ledgerService } from '../../services/ledger';
import toast from 'react-hot-toast';

const txnTypes = [
  { value: 'deposit', label: 'Deposit' },
  { value: 'withdrawal', label: 'Withdrawal' },
  { value: 'transfer', label: 'Transfer' },
  { value: 'fee', label: 'Fee' },
  { value: 'interest', label: 'Interest' },
  { value: 'loan', label: 'Loan' },
  { value: 'repayment', label: 'Repayment' },
  { value: 'other', label: 'Other' },
];

const emptyLine = () => ({ account_id: '', dr_amount: '', cr_amount: '', currency: 'INR', line_note: '' });

export default function JournalEntry() {
  const [form, setForm] = useState({
    txn_ref: '',
    txn_type: '',
    description: '',
    created_by: '',
    lines: [emptyLine(), emptyLine()],
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const setField = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const setLine = (index, field) => (e) =>
    setForm((f) => {
      const lines = [...f.lines];
      lines[index] = { ...lines[index], [field]: e.target.value };
      return { ...f, lines };
    });

  const addLine = () => setForm((f) => ({ ...f, lines: [...f.lines, emptyLine()] }));

  const removeLine = (index) => {
    if (form.lines.length <= 2) return;
    setForm((f) => ({ ...f, lines: f.lines.filter((_, i) => i !== index) }));
  };

  const totalDr = form.lines.reduce((s, l) => s + (parseFloat(l.dr_amount) || 0), 0);
  const totalCr = form.lines.reduce((s, l) => s + (parseFloat(l.cr_amount) || 0), 0);
  const isBalanced = totalDr > 0 && totalDr === totalCr;

  const validate = () => {
    const errs = {};
    if (!form.txn_type) errs.txn_type = 'Transaction type is required';
    if (form.lines.length < 2) errs.lines = 'At least 2 lines required';

    const lineErrors = form.lines.map((l) => {
      const le = {};
      if (!l.account_id) le.account_id = 'Required';
      const dr = parseFloat(l.dr_amount) || 0;
      const cr = parseFloat(l.cr_amount) || 0;
      if (dr === 0 && cr === 0) le.amount = 'Enter debit or credit';
      if (dr > 0 && cr > 0) le.amount = 'Only one side allowed';
      return le;
    });

    if (lineErrors.some((le) => Object.keys(le).length > 0)) errs.lineErrors = lineErrors;
    if (!isBalanced) errs.balance = 'Total debits must equal total credits';

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const payload = {
        txn_type: form.txn_type,
        lines: form.lines.map((l) => ({
          account_id: Number(l.account_id),
          dr_amount: parseFloat(l.dr_amount) || 0,
          cr_amount: parseFloat(l.cr_amount) || 0,
          currency: l.currency || 'INR',
          line_note: l.line_note || undefined,
        })),
      };
      if (form.txn_ref) payload.txn_ref = form.txn_ref;
      if (form.description) payload.description = form.description;
      if (form.created_by) payload.created_by = Number(form.created_by);

      const data = await ledgerService.postJournalEntry(payload);
      setResult(data);
      toast.success(`Journal entry posted: ${data.txn_ref}`);
      setForm({ txn_ref: '', txn_type: '', description: '', created_by: '', lines: [emptyLine(), emptyLine()] });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to post entry');
    } finally {
      setLoading(false);
    }
  };

  const fmt = (n) => new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2 }).format(n);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Journal Entry</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Post double-entry journal transactions
        </p>
      </div>

      {result && (
        <Card className="border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-900/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">Entry Posted Successfully</p>
              <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
                Ref: {result.txn_ref} | Status: {result.status} | Dr: {fmt(result.total_debit)} | Cr: {fmt(result.total_credit)}
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setResult(null)}>Dismiss</Button>
          </div>
        </Card>
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Input label="Transaction Ref (optional)" placeholder="Auto-generated if empty" value={form.txn_ref} onChange={setField('txn_ref')} />
            <Select label="Transaction Type" value={form.txn_type} onChange={setField('txn_type')} options={txnTypes} placeholder="Select type" error={errors.txn_type} />
            <Input label="Description" placeholder="Optional description" value={form.description} onChange={setField('description')} />
            <Input label="Created By (User ID)" type="number" placeholder="Optional" value={form.created_by} onChange={setField('created_by')} />
          </div>

          <div>
            <CardHeader className="!mb-3">
              <CardTitle>Journal Lines</CardTitle>
              <Button type="button" variant="outline" size="sm" onClick={addLine}>
                <Plus className="h-4 w-4" /> Add Line
              </Button>
            </CardHeader>
            {errors.lines && <p className="mb-2 text-xs text-red-500">{errors.lines}</p>}
            {errors.balance && <p className="mb-2 text-xs text-red-500">{errors.balance}</p>}

            <div className="space-y-3">
              {form.lines.map((line, i) => {
                const lineErr = errors.lineErrors?.[i] || {};
                return (
                  <div key={i} className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/50">
                    <div className="w-20 shrink-0">
                      <Input label="Account ID" type="number" placeholder="ID" value={line.account_id} onChange={setLine(i, 'account_id')} error={lineErr.account_id} />
                    </div>
                    <div className="w-32">
                      <Input label="Debit" type="number" step="0.01" min="0" placeholder="0.00" value={line.dr_amount} onChange={setLine(i, 'dr_amount')} error={lineErr.amount} />
                    </div>
                    <div className="w-32">
                      <Input label="Credit" type="number" step="0.01" min="0" placeholder="0.00" value={line.cr_amount} onChange={setLine(i, 'cr_amount')} />
                    </div>
                    <div className="flex-1">
                      <Input label="Note" placeholder="Optional note" value={line.line_note} onChange={setLine(i, 'line_note')} />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeLine(i)}
                      disabled={form.lines.length <= 2}
                      className="mb-0.5 text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 flex items-center justify-between rounded-lg bg-gray-100 px-4 py-3 dark:bg-gray-800">
              <div className="flex items-center gap-4 text-sm">
                <span>Total Debit: <strong className="text-amber-600 dark:text-amber-400">{fmt(totalDr)}</strong></span>
                <span>Total Credit: <strong className="text-emerald-600 dark:text-emerald-400">{fmt(totalCr)}</strong></span>
              </div>
              <Badge color={isBalanced ? 'green' : totalDr === 0 ? 'gray' : 'red'}>
                {isBalanced ? 'Balanced' : 'Unbalanced'}
              </Badge>
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setForm({ txn_ref: '', txn_type: '', description: '', created_by: '', lines: [emptyLine(), emptyLine()] })}
            >
              Reset
            </Button>
            <Button type="submit" loading={loading} disabled={!isBalanced}>
              <FileText className="h-4 w-4" /> Post Entry
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
