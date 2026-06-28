import { useState } from 'react';
import { Coins, Wallet, Hash, CalendarClock, Download, Plus } from 'lucide-react';
import Card, { CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Modal from '../../components/ui/Modal';
import EmptyState from '../../components/ui/EmptyState';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useApi } from '../../hooks/useApi';
import { useRazorpay } from '../../hooks/useRazorpay';
import { sharesService } from '../../services/shares';
import { useAuthStore } from '../../store/authStore';
import { fmtINR, fmtNum } from '../../utils/format';
import { exportToCsv } from '../../utils/exportCsv';
import toast from 'react-hot-toast';

const fmtDate = (d) => (d ? new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—');
const TYPE_LABEL = { monthly_share_deposit: 'Deposit', withdrawal: 'Withdrawal', dividend: 'Dividend' };
const labelFor = (t) => TYPE_LABEL[String(t).toLowerCase()] || t;
const isDebit = (t) => String(t).toLowerCase() === 'withdrawal';

export default function MyShares() {
  const { memberId } = useAuthStore();
  const { data, loading, execute: refresh } = useApi(() => sharesService.getMemberShares(memberId));
  const { pay, loading: paying } = useRazorpay();
  const [payOpen, setPayOpen] = useState(false);
  const [amount, setAmount] = useState('');

  if (loading) return <div className="space-y-4"><CardSkeleton /><CardSkeleton /></div>;

  const balance = Number(data?.balance ?? 0);
  const txns = data?.transactions ?? [];
  const deposits = txns.filter((t) => !isDebit(t.txn_type)).length;
  const lastDate = txns[0]?.txn_date;

  const handlePay = () => {
    const amt = Math.floor(Number(amount) || 0);
    if (amt <= 0) { toast.error('Enter an amount greater than ₹0'); return; }
    // purpose share_purchase; entity_id is the member's own id (server uses member context)
    pay('share_purchase', memberId, amt, () => { setPayOpen(false); setAmount(''); refresh(); });
  };

  const handleExport = () => {
    if (txns.length === 0) { toast.error('Nothing to export'); return; }
    const headers = ['Transaction ID', 'Date', 'Type', 'Amount (INR)', 'Remarks'];
    const rows = txns.map((t) => [t.transaction_id, fmtDate(t.txn_date), labelFor(t.txn_type), Number(t.amount).toFixed(2), t.remarks || '']);
    rows.push([]);
    rows.push(['Account balance', '', balance.toFixed(2), '']);
    exportToCsv('my-share-money-statement.csv', headers, rows);
    toast.success('Statement exported');
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">My Share Money</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Your monthly contributions and balance</p>
        </div>
        <Button onClick={() => setPayOpen(true)}>
          <Plus className="h-4 w-4" /> Pay Share Money
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <SummaryTile icon={Wallet} tone="emerald" label="Account Balance" value={fmtINR(balance)} />
        <SummaryTile icon={Hash} tone="blue" label="Deposits Made" value={fmtNum(deposits)} />
        <SummaryTile icon={CalendarClock} tone="violet" label="Last Deposit" value={lastDate ? fmtDate(lastDate) : '—'} />
      </div>

      <Card className="!p-0">
        <div className="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-800">
          <CardTitle>Statement</CardTitle>
          <Button variant="outline" size="sm" onClick={handleExport} disabled={txns.length === 0}>
            <Download className="h-4 w-4" /> Export to Excel
          </Button>
        </div>
        {txns.length === 0 ? (
          <div className="p-4"><EmptyState icon={Coins} title="No share money yet" description="Your monthly contributions will appear here once recorded." /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] text-sm">
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

      <Modal isOpen={payOpen} onClose={() => setPayOpen(false)} title="Pay Share Money" size="md">
        <div className="space-y-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Add your monthly share contribution. Payment is processed securely via Razorpay.
          </p>
          <Input
            label="Amount (₹)"
            type="number"
            min="1"
            step="1"
            placeholder="500"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setPayOpen(false)}>Cancel</Button>
            <Button loading={paying} disabled={!(Number(amount) > 0)} onClick={handlePay}>
              Pay {Number(amount) > 0 ? fmtINR(Math.floor(Number(amount))) : ''}
            </Button>
          </div>
        </div>
      </Modal>
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
