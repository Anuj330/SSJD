import { useEffect, useState } from 'react';
import { Wallet, HandCoins, Coins, CreditCard, PiggyBank, Check } from 'lucide-react';
import Card, { CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import EmptyState from '../../components/ui/EmptyState';
import { useApi } from '../../hooks/useApi';
import { useAuthStore } from '../../store/authStore';
import { membersService } from '../../services/members';
import { loansService } from '../../services/loans';
import { collectionsService } from '../../services/collections';
import { sharesService } from '../../services/shares';
import { fmtINR } from '../../utils/format';
import toast from 'react-hot-toast';

const n = (v) => Number(v) || 0;

export default function CollectPayment() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';

  const { data: membersData } = useApi(() => membersService.list());
  const memberList = Array.isArray(membersData) ? membersData : membersData?.members ?? [];

  const [memberId, setMemberId] = useState('');
  const [loans, setLoans] = useState([]);
  const [advance, setAdvance] = useState(0);
  const [shareBal, setShareBal] = useState(0);

  const [total, setTotal] = useState('');
  const [loanId, setLoanId] = useState('');
  const [loanAmt, setLoanAmt] = useState('');
  const [shareCd, setShareCd] = useState('');
  const [shareOd, setShareOd] = useState('');
  const [advanceAmt, setAdvanceAmt] = useState('');
  const [txnDate, setTxnDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [remarks, setRemarks] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const member = memberList.find((m) => String(m.id) === String(memberId));

  // Load the member's active loans + wallet balances when selected.
  useEffect(() => {
    if (!memberId) { setLoans([]); setAdvance(0); setShareBal(0); setLoanId(''); return; }
    loansService.list({ member_id: memberId, status: 'active' })
      .then((r) => { const a = (Array.isArray(r) ? r : []).filter((l) => l.status === 'active'); setLoans(a); setLoanId(a[0] ? String(a[0].id) : ''); })
      .catch(() => setLoans([]));
    collectionsService.getAdvance(memberId).then((r) => setAdvance(n(r.balance))).catch(() => setAdvance(0));
    sharesService.getMemberShares(memberId).then((r) => setShareBal(n(r.balance))).catch(() => setShareBal(0));
  }, [memberId]);

  // Prefill loan EMI with the selected loan's next due amount (incl late fee).
  useEffect(() => {
    if (!loanId) return;
    loansService.getSchedule(loanId).then((r) => {
      const next = (r.schedule || []).find((x) => !x.is_paid);
      if (next) setLoanAmt(Number(next.amount_due).toFixed(2));
    }).catch(() => {});
  }, [loanId]);

  const shareAmt = n(shareCd) + n(shareOd);   // Share money (SM) = CD + OD
  const allocated = n(loanAmt) + shareAmt + n(advanceAmt);
  const diff = n(total) - allocated;
  const balanced = n(total) > 0 && Math.abs(diff) < 0.005;

  // Convenience: dump whatever is unallocated into the advance wallet.
  const sendRestToAdvance = () => {
    const rest = n(total) - n(loanAmt) - shareAmt;
    setAdvanceAmt(rest > 0 ? rest.toFixed(2) : '0');
  };

  const submit = async () => {
    if (!memberId) return toast.error('Select a member');
    if (n(total) <= 0) return toast.error('Enter the total amount received');
    if (!balanced) return toast.error(`Allocations must equal the total (off by ${fmtINR(Math.abs(diff))})`);
    if (n(loanAmt) > 0 && !loanId) return toast.error('Select a loan for the EMI amount');
    setSubmitting(true);
    try {
      const res = await collectionsService.collect(Number(memberId), {
        total: n(total),
        loan_id: n(loanAmt) > 0 ? Number(loanId) : undefined,
        loan_amount: n(loanAmt),
        share_amount: shareAmt,
        share_cd: n(shareCd),
        share_od: n(shareOd),
        advance_amount: n(advanceAmt),
        txn_date: txnDate,
        remarks: remarks.trim() || undefined,
      });
      const bits = [];
      if (res.loan) bits.push(`EMI ${fmtINR(res.loan.amount_applied)}`);
      if (res.share) bits.push(`share ${fmtINR(shareAmt)}`);
      if (res.advance) bits.push(`advance ${fmtINR(advanceAmt)}`);
      toast.success(`Collected ${fmtINR(n(total))} — ${bits.join(' · ')}`);
      // reset amounts, refresh balances
      setTotal(''); setLoanAmt(''); setShareCd(''); setShareOd(''); setAdvanceAmt(''); setRemarks('');
      collectionsService.getAdvance(memberId).then((r) => setAdvance(n(r.balance))).catch(() => {});
      sharesService.getMemberShares(memberId).then((r) => setShareBal(n(r.balance))).catch(() => {});
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to record collection');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isAdmin) return <EmptyState icon={Wallet} title="Admins only" description="Collections are recorded by administrators." />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">Collect Payment</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Record one payment from a member and split it across their loan EMI, share money, and advance balance.</p>
      </div>

      <Card>
        <Select
          label="Select member"
          value={memberId}
          onChange={(e) => setMemberId(e.target.value)}
          options={memberList.map((m) => ({ value: String(m.id), label: `${m.name} (#${m.id})` }))}
          placeholder="Choose a member…"
        />
        {member && (
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <Tile icon={PiggyBank} tone="emerald" label="Share balance" value={fmtINR(shareBal)} />
            <Tile icon={CreditCard} tone="amber" label="Active loans" value={String(loans.length)} />
            <Tile icon={Wallet} tone="violet" label="Advance balance" value={fmtINR(advance)} />
          </div>
        )}
      </Card>

      {!memberId ? (
        <Card><EmptyState icon={HandCoins} title="No member selected" description="Pick a member to record a collection." /></Card>
      ) : (
        <>
          <Card>
            <div className="grid gap-4 sm:grid-cols-3">
              <Input label="Total received (₹)" type="number" min="1" step="1" placeholder="2000" value={total} onChange={(e) => setTotal(e.target.value)} />
              <Input label="Payment date" type="date" value={txnDate} onChange={(e) => setTxnDate(e.target.value)} />
              <Input label="Remarks (optional)" placeholder="e.g. cash at branch" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
            </div>
          </Card>

          <Card className="!p-0">
            <div className="border-b border-gray-200 p-4 dark:border-gray-800"><CardTitle>Allocate</CardTitle></div>
            <div className="space-y-4 p-4">
              {/* Loan EMI */}
              <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
                <Select
                  label="Loan (EMI)"
                  value={loanId}
                  onChange={(e) => setLoanId(e.target.value)}
                  options={loans.map((l) => ({ value: String(l.id), label: `${l.loan_number} · out ${fmtINR(l.outstanding_principal)}` }))}
                  placeholder={loans.length ? 'Select loan' : 'No active loans'}
                />
                <Input label="EMI amount (₹)" type="number" min="0" step="1" value={loanAmt} onChange={(e) => setLoanAmt(e.target.value)} placeholder="0" />
                <div className="pb-1 text-xs text-gray-400"><CreditCard className="mb-0.5 h-4 w-4" /></div>
              </div>
              {/* Share money = CD + OD */}
              <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
                <div className="flex items-end text-sm font-medium text-gray-600 dark:text-gray-300"><Coins className="mr-2 h-4 w-4 text-primary-500" /> Share money (CD + OD = {fmtINR(shareAmt)})</div>
                <div className="grid grid-cols-2 gap-2">
                  <Input label="CD (₹)" type="number" min="0" step="1" value={shareCd} onChange={(e) => setShareCd(e.target.value)} placeholder="0" />
                  <Input label="OD (₹)" type="number" min="0" step="1" value={shareOd} onChange={(e) => setShareOd(e.target.value)} placeholder="0" />
                </div>
                <div />
              </div>
              {/* Advance */}
              <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
                <div className="flex items-end text-sm font-medium text-gray-600 dark:text-gray-300"><Wallet className="mr-2 h-4 w-4 text-violet-500" /> Advance (adjust balance)</div>
                <Input label="Advance amount (₹)" type="number" min="0" step="1" value={advanceAmt} onChange={(e) => setAdvanceAmt(e.target.value)} placeholder="0" />
                <Button variant="outline" size="sm" onClick={sendRestToAdvance} className="mb-1">Fill rest</Button>
              </div>

              {/* Balance indicator */}
              <div className={`flex items-center justify-between rounded-xl border p-3 text-sm ${balanced ? 'border-primary-200 bg-primary-50 dark:border-primary-900/40 dark:bg-primary-900/20' : 'border-amber-200 bg-amber-50 dark:border-amber-900/40 dark:bg-amber-900/20'}`}>
                <span className="text-gray-600 dark:text-gray-300">Allocated <strong className="num">{fmtINR(allocated)}</strong> of <strong className="num">{fmtINR(n(total))}</strong></span>
                <span className={`num font-semibold ${balanced ? 'text-primary-600 dark:text-primary-400' : 'text-amber-600 dark:text-amber-400'}`}>
                  {balanced ? <span className="inline-flex items-center gap-1"><Check className="h-4 w-4" /> Balanced</span> : `${diff > 0 ? 'Unallocated' : 'Over by'} ${fmtINR(Math.abs(diff))}`}
                </span>
              </div>

              <Button onClick={submit} loading={submitting} disabled={!balanced} className="w-full justify-center">
                <HandCoins className="h-4 w-4" /> Record collection {n(total) > 0 ? fmtINR(n(total)) : ''}
              </Button>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function Tile({ icon: Icon, label, value, tone }) {
  const tones = {
    emerald: 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300',
    amber: 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-300',
    violet: 'bg-violet-50 text-violet-600 dark:bg-violet-900/30 dark:text-violet-300',
  };
  return (
    <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900">
      <span className={`flex h-10 w-10 items-center justify-center rounded-lg ${tones[tone]}`}><Icon className="h-5 w-5" /></span>
      <div><div className="text-xs text-gray-500 dark:text-gray-400">{label}</div><div className="num text-lg font-bold text-gray-900 dark:text-gray-100">{value}</div></div>
    </div>
  );
}
