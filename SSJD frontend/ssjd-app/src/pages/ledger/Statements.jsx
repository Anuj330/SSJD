import { useState } from 'react';
import { Search } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Badge from '../../components/ui/Badge';
import DataTable from '../../components/ui/DataTable';
import { ledgerService } from '../../services/ledger';
import { membersService } from '../../services/members';
import toast from 'react-hot-toast';

export default function Statements() {
  const [tab, setTab] = useState('account');
  const [accountId, setAccountId] = useState('');
  const [memberId, setMemberId] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const fetchAccountStatement = async () => {
    if (!accountId) { toast.error('Enter an account ID'); return; }
    setLoading(true);
    try {
      const result = await ledgerService.getAccountStatement(accountId, fromDate || undefined, toDate || undefined);
      setData({ type: 'account', ...result });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to fetch statement');
    } finally {
      setLoading(false);
    }
  };

  const fetchMoneyFlow = async () => {
    if (!memberId) { toast.error('Enter a member ID'); return; }
    setLoading(true);
    try {
      const result = await membersService.getMoneyFlow(memberId, fromDate || undefined, toDate || undefined);
      setData({ type: 'member', ...result });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to fetch money flow');
    } finally {
      setLoading(false);
    }
  };

  const accountColumns = [
    { key: 'txn_ref', label: 'Txn Ref', render: (v) => <span className="font-mono text-xs">{v}</span> },
    { key: 'txn_type', label: 'Type', render: (v) => <Badge color="blue">{v}</Badge> },
    {
      key: 'dr_amount',
      label: 'Debit',
      render: (v) => Number(v) > 0 ? <span className="font-mono text-amber-600 dark:text-amber-400">{fmt(v)}</span> : '-',
    },
    {
      key: 'cr_amount',
      label: 'Credit',
      render: (v) => Number(v) > 0 ? <span className="font-mono text-emerald-600 dark:text-emerald-400">{fmt(v)}</span> : '-',
    },
    { key: 'currency', label: 'Currency' },
    { key: 'line_note', label: 'Note' },
    {
      key: 'created_at',
      label: 'Date',
      render: (v) => v ? new Date(v).toLocaleDateString('en-IN') : '-',
    },
  ];

  const memberColumns = [
    { key: 'txn_ref', label: 'Txn Ref', render: (v) => <span className="font-mono text-xs">{v}</span> },
    { key: 'txn_type', label: 'Type', render: (v) => <Badge color="blue">{v}</Badge> },
    { key: 'account_name', label: 'Account' },
    { key: 'account_code', label: 'Code', render: (v) => <span className="font-mono text-xs">{v}</span> },
    {
      key: 'dr_amount',
      label: 'Debit',
      render: (v) => Number(v) > 0 ? <span className="font-mono text-amber-600 dark:text-amber-400">{fmt(v)}</span> : '-',
    },
    {
      key: 'cr_amount',
      label: 'Credit',
      render: (v) => Number(v) > 0 ? <span className="font-mono text-emerald-600 dark:text-emerald-400">{fmt(v)}</span> : '-',
    },
    {
      key: 'created_at',
      label: 'Date',
      render: (v) => v ? new Date(v).toLocaleDateString('en-IN') : '-',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Statements</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          View account statements and member money flow
        </p>
      </div>

      <Card>
        <div className="mb-6 flex rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
          {[
            { key: 'account', label: 'Account Statement' },
            { key: 'member', label: 'Member Money Flow' },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => { setTab(t.key); setData(null); }}
              className={`flex-1 rounded-md py-2 text-sm font-medium transition-all ${
                tab === t.key
                  ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-end gap-3">
          {tab === 'account' ? (
            <Input label="Account ID" type="number" placeholder="Enter account ID" value={accountId} onChange={(e) => setAccountId(e.target.value)} />
          ) : (
            <Input label="Member ID" type="number" placeholder="Enter member ID" value={memberId} onChange={(e) => setMemberId(e.target.value)} />
          )}
          <Input label="From Date" type="datetime-local" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          <Input label="To Date" type="datetime-local" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          <Button onClick={tab === 'account' ? fetchAccountStatement : fetchMoneyFlow} loading={loading}>
            <Search className="h-4 w-4" /> Fetch
          </Button>
        </div>
      </Card>

      {data && (
        <Card>
          <CardHeader>
            <CardTitle>
              {data.type === 'account'
                ? `${data.account_name} (${data.account_code})`
                : `Member #${data.member_id}`}
            </CardTitle>
            <div className="flex items-center gap-4 text-sm">
              <span>Dr: <strong className="text-amber-600 dark:text-amber-400">{fmt(data.total_debit)}</strong></span>
              <span>Cr: <strong className="text-emerald-600 dark:text-emerald-400">{fmt(data.total_credit)}</strong></span>
              {data.net_credit_minus_debit !== undefined && (
                <span>
                  Net:{' '}
                  <strong className={Number(data.net_credit_minus_debit) >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                    {fmt(data.net_credit_minus_debit)}
                  </strong>
                </span>
              )}
            </div>
          </CardHeader>
          <DataTable
            columns={data.type === 'account' ? accountColumns : memberColumns}
            data={data.rows ?? []}
            pageSize={15}
            emptyMessage="No transactions found"
          />
        </Card>
      )}
    </div>
  );
}
