import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Wallet,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Calendar,
  Download,
} from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Input from '../../components/ui/Input';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useApi } from '../../hooks/useApi';
import { useAuthStore } from '../../store/authStore';
import { membersService } from '../../services/members';

const txnTypeLabels = {
  deposit_open: 'Opening Deposit',
  deposit: 'Deposit',
  withdrawal: 'Withdrawal',
  interest_credit: 'Interest Credit',
  deposit_close: 'Account Closure',
  reversal: 'Reversal',
};

const txnTypeColors = {
  deposit_open: 'green',
  deposit: 'green',
  withdrawal: 'red',
  interest_credit: 'blue',
  deposit_close: 'gray',
  reversal: 'yellow',
};

export default function MemberPassbook() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { role, memberId: authMemberId } = useAuthStore();
  const isAdmin = role === 'admin';

  // For members, always use their own ID
  const targetId = isAdmin ? id : authMemberId;

  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const {
    data: passbook,
    loading,
    execute: refresh,
  } = useApi(() => membersService.getPassbook(targetId, fromDate || undefined, toDate || undefined), [
    targetId,
    fromDate,
    toDate,
  ]);

  const rows = passbook?.rows ?? [];
  const monthly = passbook?.monthly_summary ?? [];

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);

  const fmtShort = (n) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(n);

  // ─── Summary cards ───
  const summaryCards = [
    {
      label: 'Total Credited',
      value: fmtShort(passbook?.total_credited ?? 0),
      icon: TrendingUp,
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-900/30',
    },
    {
      label: 'Total Debited',
      value: fmtShort(passbook?.total_debited ?? 0),
      icon: TrendingDown,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-900/30',
    },
    {
      label: 'Total Penalty',
      value: fmtShort(passbook?.total_penalty ?? 0),
      icon: AlertTriangle,
      color: 'text-red-600 dark:text-red-400',
      bg: 'bg-red-50 dark:bg-red-900/30',
    },
    {
      label: 'Current Balance',
      value: fmtShort(passbook?.current_balance ?? 0),
      icon: Wallet,
      color:
        Number(passbook?.current_balance ?? 0) >= 0
          ? 'text-emerald-600 dark:text-emerald-400'
          : 'text-red-600 dark:text-red-400',
      bg:
        Number(passbook?.current_balance ?? 0) >= 0
          ? 'bg-emerald-50 dark:bg-emerald-900/30'
          : 'bg-red-50 dark:bg-red-900/30',
    },
  ];

  // ─── Tab state ───
  const [tab, setTab] = useState('transactions');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          {isAdmin && (
            <Button variant="ghost" size="sm" onClick={() => navigate(`/members/${id}`)}>
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {passbook?.member_name ? `${passbook.member_name}'s Passbook` : 'My Passbook'}
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {passbook?.transaction_count ?? 0} transactions
            </p>
          </div>
        </div>
        {targetId && (
          <a
            href={`/api/v1/pdf/passbook/${targetId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-800"
          >
            <Download className="h-4 w-4" /> Download PDF
          </a>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
          : summaryCards.map((stat) => {
              const Icon = stat.icon;
              return (
                <Card key={stat.label} className="relative overflow-hidden">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                        {stat.label}
                      </p>
                      <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">
                        {stat.value}
                      </p>
                    </div>
                    <div className={`rounded-lg p-2.5 ${stat.bg}`}>
                      <Icon className={`h-5 w-5 ${stat.color}`} />
                    </div>
                  </div>
                </Card>
              );
            })}
      </div>

      {/* Date Filters */}
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <Input
              label="From Date"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
            />
          </div>
          <div className="flex-1">
            <Input
              label="To Date"
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
            />
          </div>
          <Button
            variant="secondary"
            onClick={() => {
              setFromDate('');
              setToDate('');
            }}
          >
            Clear
          </Button>
        </div>
      </Card>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {[
          { key: 'transactions', label: 'All Transactions' },
          { key: 'monthly', label: 'Monthly Summary' },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'border-b-2 border-primary-600 text-primary-600 dark:text-primary-400'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {tab === 'transactions' ? (
        <TransactionsTable rows={rows} loading={loading} fmt={fmt} />
      ) : (
        <MonthlySummaryTable monthly={monthly} loading={loading} fmt={fmt} fmtShort={fmtShort} />
      )}
    </div>
  );
}

// ─── Transactions Table (passbook-style) ───

function TransactionsTable({ rows, loading, fmt }) {
  if (loading) {
    return (
      <Card>
        <div className="space-y-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          ))}
        </div>
      </Card>
    );
  }

  if (rows.length === 0) {
    return (
      <Card>
        <div className="py-12 text-center">
          <Wallet className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-600" />
          <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">No transactions found.</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
            <tr>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">#</th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Date</th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Type</th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">
                Description
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">
                Credited
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">
                Debited
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">
                Penalty
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">
                Balance
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {rows.map((row, i) => {
              const typeLabel = txnTypeLabels[row.txn_type] || row.txn_type;
              const typeColor = txnTypeColors[row.txn_type] || 'gray';
              const cr = Number(row.credit);
              const dr = Number(row.debit);
              const pen = Number(row.penalty);
              const bal = Number(row.running_balance);

              return (
                <tr
                  key={i}
                  className={`bg-white transition-colors dark:bg-gray-900 ${
                    row.is_penalty
                      ? 'bg-red-50/50 dark:bg-red-900/10'
                      : ''
                  }`}
                >
                  <td className="px-4 py-3 text-xs text-gray-400">{i + 1}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-gray-700 dark:text-gray-300">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-gray-400" />
                      {row.date
                        ? new Date(row.date).toLocaleDateString('en-IN', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                          })
                        : '-'}
                    </div>
                    <p className="mt-0.5 text-[10px] text-gray-400">
                      {row.date
                        ? new Date(row.date).toLocaleTimeString('en-IN', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : ''}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <Badge color={typeColor}>{typeLabel}</Badge>
                  </td>
                  <td className="max-w-[200px] px-4 py-3">
                    <p className="truncate text-gray-700 dark:text-gray-300">{row.description || '-'}</p>
                    <p className="mt-0.5 font-mono text-[10px] text-gray-400">{row.txn_ref}</p>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    {cr > 0 ? (
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        +{fmt(cr)}
                      </span>
                    ) : (
                      <span className="text-gray-300 dark:text-gray-600">-</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    {dr > 0 ? (
                      <span className="font-semibold text-amber-600 dark:text-amber-400">
                        -{fmt(dr)}
                      </span>
                    ) : (
                      <span className="text-gray-300 dark:text-gray-600">-</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    {pen > 0 ? (
                      <span className="font-semibold text-red-600 dark:text-red-400">
                        {fmt(pen)}
                      </span>
                    ) : (
                      <span className="text-gray-300 dark:text-gray-600">-</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <span
                      className={`font-bold ${
                        bal >= 0
                          ? 'text-gray-900 dark:text-gray-100'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {fmt(bal)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
          {/* Footer totals */}
          <tfoot className="border-t-2 border-gray-300 bg-gray-50 font-semibold dark:border-gray-600 dark:bg-gray-800/50">
            <tr>
              <td colSpan={4} className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                Totals
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-emerald-600 dark:text-emerald-400">
                {fmt(rows.reduce((s, r) => s + Number(r.credit), 0))}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-amber-600 dark:text-amber-400">
                {fmt(rows.reduce((s, r) => s + Number(r.debit), 0))}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-red-600 dark:text-red-400">
                {fmt(rows.reduce((s, r) => s + Number(r.penalty), 0))}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right font-bold text-gray-900 dark:text-gray-100">
                {rows.length > 0 ? fmt(Number(rows[rows.length - 1].running_balance)) : fmt(0)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </Card>
  );
}

// ─── Monthly Summary Table ───

function MonthlySummaryTable({ monthly, loading, fmt, fmtShort }) {
  if (loading) {
    return (
      <Card>
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          ))}
        </div>
      </Card>
    );
  }

  if (monthly.length === 0) {
    return (
      <Card>
        <div className="py-12 text-center">
          <Calendar className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-600" />
          <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">No monthly data available.</p>
        </div>
      </Card>
    );
  }

  const monthLabel = (ym) => {
    const [year, month] = ym.split('-');
    const date = new Date(Number(year), Number(month) - 1);
    return date.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
  };

  return (
    <Card className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
            <tr>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Month</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-600 dark:text-gray-400">
                Transactions
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">
                Credited
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">
                Debited
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">
                Penalty
              </th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">
                Net
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {monthly.map((m) => {
              const net = Number(m.total_credit) - Number(m.total_debit);
              return (
                <tr key={m.month} className="bg-white dark:bg-gray-900">
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                    {monthLabel(m.month)}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-600 dark:text-gray-400">
                    {m.txn_count}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right font-medium text-emerald-600 dark:text-emerald-400">
                    {fmt(m.total_credit)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right font-medium text-amber-600 dark:text-amber-400">
                    {fmt(m.total_debit)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right font-medium text-red-600 dark:text-red-400">
                    {Number(m.penalty) > 0 ? fmt(m.penalty) : '-'}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <span
                      className={`font-bold ${
                        net >= 0
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {net >= 0 ? '+' : ''}{fmt(net)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
