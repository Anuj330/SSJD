import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Input from '../../components/ui/Input';
import DataTable from '../../components/ui/DataTable';
import { useApi } from '../../hooks/useApi';
import { ledgerService } from '../../services/ledger';

const typeColors = {
  asset: 'blue',
  liability: 'red',
  income: 'green',
  expense: 'yellow',
  equity: 'purple',
};

export default function TrialBalance() {
  const [asOf, setAsOf] = useState('');
  const { data, loading, execute: refresh } = useApi(() => ledgerService.getTrialBalance(asOf || undefined), [asOf]);

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const columns = [
    { key: 'account_code', label: 'Code', render: (v) => <span className="font-mono text-xs">{v}</span> },
    { key: 'account_name', label: 'Account', render: (v) => <span className="font-medium">{v}</span> },
    { key: 'account_type', label: 'Type', render: (v) => <Badge color={typeColors[v] || 'gray'}>{v}</Badge> },
    {
      key: 'total_debit',
      label: 'Debit',
      render: (v) => <span className="font-mono text-amber-600 dark:text-amber-400">{fmt(v)}</span>,
    },
    {
      key: 'total_credit',
      label: 'Credit',
      render: (v) => <span className="font-mono text-emerald-600 dark:text-emerald-400">{fmt(v)}</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Trial Balance</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Verify that debits equal credits across all accounts
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Input type="datetime-local" value={asOf} onChange={(e) => setAsOf(e.target.value)} className="w-auto" />
          <Button variant="outline" size="sm" onClick={() => refresh()}>
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        </div>
      </div>

      {data && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">Total Debits</p>
            <p className="mt-1 text-2xl font-bold text-amber-600 dark:text-amber-400">{fmt(data.total_debit)}</p>
          </Card>
          <Card className="text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">Total Credits</p>
            <p className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{fmt(data.total_credit)}</p>
          </Card>
          <Card className="text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
            <div className="mt-2">
              <Badge color={data.is_balanced ? 'green' : 'red'} className="text-base">
                {data.is_balanced ? 'Balanced' : 'Unbalanced'}
              </Badge>
            </div>
          </Card>
        </div>
      )}

      <Card>
        <DataTable
          columns={columns}
          data={data?.rows ?? []}
          loading={loading}
          pageSize={20}
          emptyMessage="No accounts with transactions"
        />
      </Card>
    </div>
  );
}
