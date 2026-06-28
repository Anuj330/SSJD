import { useEffect, useState } from 'react';
import { Coins, Plus, Download, Wallet, CalendarClock, Hash } from 'lucide-react';
import Card, { CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import EmptyState from '../../components/ui/EmptyState';
import { useApi } from '../../hooks/useApi';
import { useAuthStore } from '../../store/authStore';
import { sharesService } from '../../services/shares';
import { membersService } from '../../services/members';
import { fmtINR, fmtNum } from '../../utils/format';
import { exportToCsv } from '../../utils/exportCsv';
import toast from 'react-hot-toast';

const fmtDate = (d) => (d ? new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—');

const TYPE_LABEL = { monthly_share_deposit: 'Deposit', withdrawal: 'Withdrawal', dividend: 'Dividend' };
const labelFor = (t) => TYPE_LABEL[String(t).toLowerCase()] || t;
const isDebit = (t) => String(t).toLowerCase() === 'withdrawal';

export default function SharesPage() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';

  const { data: membersData } = useApi(() => membersService.list());
  const memberList = Array.isArray(membersData) ? membersData : membersData?.members ?? [];

  const [memberId, setMemberId] = useState('');
  const [shareData, setShareData] = useState(null);
  const [loadingShares, setLoadingShares] = useState(false);

  const [amount, setAmount] = useState('');
  const [remarks, setRemarks] = useState('');
  const [txnDate, setTxnDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [submitting, setSubmitting] = useState(false);

  const selectedMember = memberList.find((m) => String(m.id) === String(memberId));
  const amt = Number(amount) || 0;
  const afterCutoff = txnDate && Number(txnDate.slice(8, 10)) > 15;

  async function loadShares(id) {
    if (!id) { setShareData(null); return; }
    setLoadingShares(true);
    try {
      setShareData(await sharesService.getMemberShares(id));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load statement');
      setShareData(null);
    } finally {
      setLoadingShares(false);
    }
  }

  useEffect(() => { loadShares(memberId); /* eslint-disable-next-line */ }, [memberId]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!memberId) { toast.error('Select a member first'); return; }
    if (amt <= 0) { toast.error('Enter an amount greater than ₹0'); return; }
    setSubmitting(true);
    try {
      await sharesService.addShareMoney(Number(memberId), amt, remarks.trim(), txnDate);
      toast.success(`Deposited ${fmtINR(amt)} to ${selectedMember?.name}'s account`);
      setAmount('');
      setRemarks('');
      await loadShares(memberId);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add share money');
    } finally {
      setSubmitting(false);
    }
  };

  const txns = shareData?.transactions ?? [];
  const balance = Number(shareData?.balance ?? 0);
  const deposits = txns.filter((t) => !isDebit(t.txn_type)).length;
  const lastDate = txns[0]?.txn_date;

  const handleExport = () => {
    if (!shareData || txns.length === 0) { toast.error('Nothing to export'); return; }
    const headers = ['Transaction ID', 'Date', 'Type', 'Amount (INR)', 'Remarks'];
    const rows = txns.map((t) => [t.transaction_id, fmtDate(t.txn_date), labelFor(t.txn_type), Number(t.amount).toFixed(2), t.remarks || '']);
    rows.push([]);
    rows.push(['Account balance', '', balance.toFixed(2), '']);
    const safeName = (selectedMember?.name || `member-${memberId}`).replace(/\s+/g, '-').toLowerCase();
    exportToCsv(`share-money-statement-${safeName}.csv`, headers, rows);
    toast.success('Statement exported');
  };

  if (!isAdmin) {
    return <EmptyState icon={Coins} title="Admins only" description="Share money management is available to administrators." />;
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">Share Money</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Record a member's monthly contribution — it accumulates as a balance in their account</p>
      </div>

      {/* Member selector + add money */}
      <Card>
        <div className="grid gap-5 lg:grid-cols-2">
          <div>
            <Select
              label="Select member"
              value={memberId}
              onChange={(e) => setMemberId(e.target.value)}
              options={memberList.map((m) => ({ value: String(m.id), label: `${m.name} (#${m.id})` }))}
              placeholder="Choose a member…"
            />
            {selectedMember && (
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                {selectedMember.phone ? <span className="num">{selectedMember.phone}</span> : 'No phone on record'}
              </p>
            )}
          </div>

          <form onSubmit={handleAdd} className="space-y-3">
            <Input
              label="Monthly share money (₹)"
              type="number"
              min="1"
              step="1"
              placeholder="500"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            <Input
              label="Deposit date"
              type="date"
              value={txnDate}
              onChange={(e) => setTxnDate(e.target.value)}
            />
            {afterCutoff && (
              <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                After the 15th — this deposit earns no interest for {new Date(txnDate).toLocaleDateString('en-IN', { month: 'long' })}.
              </p>
            )}
            <Input
              label="Remarks (optional)"
              type="text"
              placeholder="e.g. June 2026 contribution"
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
            />
            <Button type="submit" loading={submitting} disabled={!memberId || amt <= 0} className="w-full justify-center">
              <Plus className="h-4 w-4" /> Add {amt > 0 ? fmtINR(amt) : 'Share Money'}
            </Button>
          </form>
        </div>
      </Card>

      {/* Selected member statement */}
      {!memberId ? (
        <Card>
          <EmptyState icon={Coins} title="No member selected" description="Pick a member above to add share money and see their statement." />
        </Card>
      ) : (
        <>
          {/* Summary */}
          <div className="grid gap-4 sm:grid-cols-3">
            <SummaryTile icon={Wallet} tone="emerald" label="Account Balance" value={fmtINR(balance)} />
            <SummaryTile icon={Hash} tone="blue" label="Deposits Made" value={fmtNum(deposits)} />
            <SummaryTile icon={CalendarClock} tone="violet" label="Last Deposit" value={lastDate ? fmtDate(lastDate) : '—'} />
          </div>

          <Card className="!p-0">
            <div className="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-800">
              <div>
                <CardTitle>Share Money Statement</CardTitle>
                <p className="mt-0.5 text-xs text-gray-400">{selectedMember?.name} · {txns.length} entr{txns.length === 1 ? 'y' : 'ies'}</p>
              </div>
              <Button variant="outline" size="sm" onClick={handleExport} disabled={txns.length === 0}>
                <Download className="h-4 w-4" /> Export to Excel
              </Button>
            </div>

            {loadingShares ? (
              <div className="space-y-2 p-4">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-10 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />)}</div>
            ) : txns.length === 0 ? (
              <div className="p-4"><EmptyState icon={Coins} title="No entries yet" description="Add share money above to create the first deposit." /></div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left text-[11px] uppercase tracking-wide text-gray-400 dark:border-gray-800">
                      <th className="px-4 py-3 font-bold">Txn ID</th>
                      <th className="px-4 py-3 font-bold">Date</th>
                      <th className="px-4 py-3 font-bold">Type</th>
                      <th className="px-4 py-3 font-bold">Remarks</th>
                      <th className="px-4 py-3 text-right font-bold">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {txns.map((t) => {
                      const debit = isDebit(t.txn_type);
                      return (
                        <tr key={t.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50 dark:border-gray-800/60 dark:hover:bg-gray-800/40">
                          <td className="num px-4 py-3 text-[12px] text-gray-500 dark:text-gray-400">{t.transaction_id}</td>
                          <td className="num px-4 py-3 text-gray-600 dark:text-gray-300">{fmtDate(t.txn_date)}</td>
                          <td className="px-4 py-3">
                            <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${debit ? 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-300' : 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'}`}>{labelFor(t.txn_type)}</span>
                          </td>
                          <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{t.remarks || <span className="text-gray-300 dark:text-gray-600">—</span>}</td>
                          <td className={`num px-4 py-3 text-right font-bold ${debit ? 'text-red-500 dark:text-red-400' : 'text-primary-600 dark:text-primary-400'}`}>
                            {debit ? '−' : '+'}{fmtINR(t.amount)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

function SummaryTile({ icon: Icon, label, value, tone }) {
  const tones = {
    emerald: 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300',
    blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300',
    violet: 'bg-violet-50 text-violet-600 dark:bg-violet-900/30 dark:text-violet-300',
  };
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${tones[tone]}`}><Icon className="h-5 w-5" /></span>
      <div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
        <div className="num text-xl font-bold text-gray-900 dark:text-gray-100">{value}</div>
      </div>
    </div>
  );
}
