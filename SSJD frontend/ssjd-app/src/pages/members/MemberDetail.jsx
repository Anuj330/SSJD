import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Edit, Trash2, RotateCcw, Wallet, BookOpen, Coins, PiggyBank, Repeat, CreditCard } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import DataTable from '../../components/ui/DataTable';
import Ring from '../../components/ui/Ring';
import { AreaLine, Bars, Donut } from '../../components/charts/Charts';
import { CardSkeleton } from '../../components/ui/Skeleton';
import MemberForm from './MemberForm';
import { useApi } from '../../hooks/useApi';
import { membersService } from '../../services/members';
import { sharesService } from '../../services/shares';
import { depositsService } from '../../services/deposits';
import { loansService } from '../../services/loans';
import { fmtINR, fmtCompact } from '../../utils/format';
import toast from 'react-hot-toast';

const monthKey = (d) => (d ? String(d).slice(0, 7) : null);
const COLORS = { share: '#0BA371', fd: '#2F6FED', rd: '#7C5CE0', sav: '#D98E04' };
const depType = (acc) => {
  const p = String(acc || '').toUpperCase();
  if (p.startsWith('FD')) return 'fd';
  if (p.startsWith('RD')) return 'rd';
  return 'sav';
};

export default function MemberDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: member, loading, execute: refresh } = useApi(() => membersService.get(id), [id]);
  const { data: moneyFlow, loading: flowLoading } = useApi(() => membersService.getMoneyFlow(id), [id]);
  const { data: shares } = useApi(() => sharesService.getMemberShares(id), [id]);
  const { data: interest } = useApi(() => sharesService.getShareInterest(id), [id]);
  const { data: deposits } = useApi(() => depositsService.list({ member_id: id }), [id]);
  const { data: loans } = useApi(() => loansService.list({ member_id: id }), [id]);
  const [showEdit, setShowEdit] = useState(false);

  const handleDeactivate = async () => {
    if (!window.confirm('Are you sure you want to deactivate this member?')) return;
    try { await membersService.deactivate(id); toast.success('Member deactivated'); navigate('/members'); }
    catch { toast.error('Failed to deactivate'); }
  };

  const handleReactivate = async () => {
    try { await membersService.reactivate(id); toast.success('Member reactivated'); refresh(); }
    catch { toast.error('Failed to reactivate'); }
  };

  // ── Derived financials ──
  const shareBalance = Number(shares?.balance ?? 0);
  const shareTxns = Array.isArray(shares?.transactions) ? shares.transactions : [];
  // cumulative share balance by month
  const shareSeries = (() => {
    const sorted = [...shareTxns].sort((a, b) => new Date(a.reference_month || a.txn_date) - new Date(b.reference_month || b.txn_date));
    const byMonth = new Map();
    let run = 0;
    for (const t of sorted) {
      run += (String(t.txn_type).toLowerCase() === 'withdrawal' ? -1 : 1) * Number(t.amount);
      byMonth.set(monthKey(t.reference_month || t.txn_date), run);
    }
    return [...byMonth.entries()].map(([m, v]) => ({ label: (m || '').slice(2), value: Math.round(v) }));
  })();

  const depList = Array.isArray(deposits) ? deposits : [];
  const fdTotal = depList.filter((d) => depType(d.account_number) === 'fd').reduce((s, d) => s + Number(d.current_balance || 0), 0);
  const rdTotal = depList.filter((d) => depType(d.account_number) === 'rd').reduce((s, d) => s + Number(d.current_balance || 0), 0);
  const savTotal = depList.filter((d) => depType(d.account_number) === 'sav').reduce((s, d) => s + Number(d.current_balance || 0), 0);
  const depBars = depList.map((d) => ({ label: d.account_number?.slice(0, 7) || '—', value: Math.round(Number(d.current_balance || 0)) }));

  const loanList = (Array.isArray(loans) ? loans : []).filter((l) => ['active', 'disbursed'].includes(String(l.status).toLowerCase()));
  const loanOutstanding = loanList.reduce((s, l) => s + Number(l.outstanding_principal || 0), 0);

  const composition = [
    { label: 'Share Money', value: shareBalance, color: COLORS.share },
    { label: 'Fixed Deposit', value: fdTotal, color: COLORS.fd },
    { label: 'Recurring Deposit', value: rdTotal, color: COLORS.rd },
    { label: 'Savings', value: savTotal, color: COLORS.sav },
  ];
  const totalAssets = composition.reduce((s, c) => s + c.value, 0);

  const kpis = [
    { label: 'Share Money', value: fmtCompact(shareBalance), icon: Coins, color: COLORS.share },
    { label: 'Fixed Deposits', value: fmtCompact(fdTotal), icon: PiggyBank, color: COLORS.fd },
    { label: 'Recurring Deposits', value: fmtCompact(rdTotal), icon: Repeat, color: COLORS.rd },
    { label: 'Loan Outstanding', value: fmtCompact(loanOutstanding), icon: CreditCard, color: '#E5484D' },
  ];

  const flowColumns = [
    { key: 'txn_ref', label: 'Txn Ref' },
    { key: 'txn_type', label: 'Type', render: (v) => <Badge color="blue">{v}</Badge> },
    { key: 'account_name', label: 'Account' },
    { key: 'dr_amount', label: 'Debit', render: (v) => Number(v) > 0 ? <span className="text-amber-600 dark:text-amber-400">{fmtINR(v)}</span> : '-' },
    { key: 'cr_amount', label: 'Credit', render: (v) => Number(v) > 0 ? <span className="text-emerald-600 dark:text-emerald-400">{fmtINR(v)}</span> : '-' },
    { key: 'created_at', label: 'Date', render: (v) => v ? new Date(v).toLocaleDateString('en-IN') : '-' },
  ];

  if (loading) return <div className="space-y-6"><CardSkeleton /><CardSkeleton /></div>;
  if (!member) return (
    <div className="py-16 text-center text-gray-500 dark:text-gray-400">Member not found.
      <Button variant="ghost" className="mt-4" onClick={() => navigate('/members')}>Back to Members</Button>
    </div>
  );

  const panel = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 16, boxShadow: 'var(--shadow)' };
  const sectionT = (t, s) => <div><div className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>{t}</div>{s && <div className="text-[12px]" style={{ color: 'var(--text-2)' }}>{s}</div>}</div>;

  return (
    <div className="space-y-5">
      <Button variant="ghost" size="sm" onClick={() => navigate('/members')}><ArrowLeft className="h-4 w-4" /> Back</Button>

      {/* Header */}
      <Card>
        <CardHeader>
          <div>
            <div className="flex items-center gap-3"><CardTitle>{member.name}</CardTitle>
              <Badge color={member.is_active ? 'green' : 'red'}>{member.is_active ? 'Active' : 'Inactive'}</Badge></div>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Member ID: {member.id}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate(`/members/${id}/passbook`)}><BookOpen className="h-4 w-4" /> Passbook</Button>
            <Button variant="outline" size="sm" onClick={() => setShowEdit(true)}><Edit className="h-4 w-4" /> Edit</Button>
            {member.is_active
              ? <Button variant="danger" size="sm" onClick={handleDeactivate}><Trash2 className="h-4 w-4" /> Deactivate</Button>
              : <Button variant="primary" size="sm" onClick={handleReactivate}><RotateCcw className="h-4 w-4" /> Activate</Button>}
          </div>
        </CardHeader>
        <div className="grid gap-4 sm:grid-cols-3">
          {[['Phone', member.phone || 'N/A'], ['Address', member.address || 'N/A'], ['Joined', member.created_at ? new Date(member.created_at).toLocaleDateString('en-IN') : 'N/A']].map(([k, v]) => (
            <div key={k} className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
              <p className="text-xs font-medium uppercase text-gray-400">{k}</p>
              <p className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{v}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* KPI tiles */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((c) => {
          const Icon = c.icon;
          return (
            <div key={c.label} style={{ ...panel, padding: 16 }}>
              <div className="flex h-9 w-9 items-center justify-center rounded-[9px]" style={{ background: 'var(--surface-2)' }}><Icon className="h-[18px] w-[18px]" style={{ color: c.color }} /></div>
              <div className="mt-3 text-[12.5px] font-semibold" style={{ color: 'var(--text-2)' }}>{c.label}</div>
              <div className="num mt-0.5 text-[22px] font-bold" style={{ color: 'var(--text)' }}>{c.value}</div>
            </div>
          );
        })}
      </div>

      {/* Composition donut + Share money growth */}
      <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
        <div style={{ ...panel, padding: 20 }}>
          {sectionT('Holdings', 'Asset composition')}
          <div className="mt-3 flex items-center gap-4">
            <Donut data={composition} centerLabel={fmtCompact(totalAssets)} />
            <div className="flex flex-1 flex-col gap-2">
              {composition.map((c) => (
                <div key={c.label} className="flex items-center gap-2 text-[12.5px]">
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ background: c.color }} />
                  <span className="flex-1" style={{ color: 'var(--text-2)' }}>{c.label}</span>
                  <span className="num font-bold" style={{ color: 'var(--text)' }}>{fmtCompact(c.value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div style={{ ...panel, padding: 20 }}>
          {sectionT('Share Money Growth', 'Cumulative balance by month')}
          <div className="mt-2">
            {shareSeries.length > 1 ? <AreaLine data={shareSeries} /> :
              <div className="grid h-[160px] place-items-center text-[13px]" style={{ color: 'var(--text-3)' }}>Not enough share-money history to chart.</div>}
          </div>
        </div>
      </div>

      {/* Interest on share money */}
      <div style={{ ...panel, overflow: 'hidden' }}>
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: '1px solid var(--border)' }}>
          {sectionT('Interest on Share Money', 'Simple interest accrued on each monthly deposit')}
          <span className="num rounded-[7px] px-2.5 py-1 text-[12px] font-bold" style={{ color: 'var(--accent)', background: 'var(--accent-soft)' }}>
            {Number(interest?.rate ?? 6)}% p.a.
          </span>
        </div>
        <div className="grid gap-4 p-5 sm:grid-cols-3">
          {[['Principal', interest?.principal, 'var(--text)'], ['Interest Earned', interest?.total_interest, 'var(--accent)'], ['Balance + Interest', interest?.balance_with_interest, 'var(--text)']].map(([l, v, color]) => (
            <div key={l} className="rounded-xl p-4" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
              <div className="text-[12px] font-semibold" style={{ color: 'var(--text-2)' }}>{l}</div>
              <div className="num mt-1 text-[22px] font-bold" style={{ color }}>{fmtINR(Number(v ?? 0))}</div>
            </div>
          ))}
        </div>
        {Array.isArray(interest?.breakdown) && interest.breakdown.length > 0 && (
          <div className="overflow-x-auto px-2 pb-3">
            <table className="w-full min-w-[460px] text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide" style={{ color: 'var(--text-3)' }}>
                  <th className="px-4 py-2 font-bold">Deposit Month</th>
                  <th className="px-4 py-2 text-right font-bold">Amount</th>
                  <th className="px-4 py-2 text-right font-bold">Months Held</th>
                  <th className="px-4 py-2 text-right font-bold">Interest</th>
                </tr>
              </thead>
              <tbody>
                {interest.breakdown.map((b, i) => (
                  <tr key={i} style={{ borderTop: '1px solid var(--border-2)' }}>
                    <td className="num px-4 py-2" style={{ color: 'var(--text-2)' }}>{String(b.date).slice(0, 7)}</td>
                    <td className="num px-4 py-2 text-right" style={{ color: 'var(--text)' }}>{fmtINR(Number(b.amount))}</td>
                    <td className="num px-4 py-2 text-right" style={{ color: 'var(--text-2)' }}>{b.months_active}</td>
                    <td className="num px-4 py-2 text-right font-bold" style={{ color: 'var(--accent)' }}>{fmtINR(Number(b.interest))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Deposits + Loans */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div style={{ ...panel, padding: 20 }}>
          {sectionT('Deposits', `${depList.length} account${depList.length === 1 ? '' : 's'} · FD / RD / Savings`)}
          <div className="mt-2">
            {depBars.length ? <Bars data={depBars} /> :
              <div className="grid h-[160px] place-items-center text-[13px]" style={{ color: 'var(--text-3)' }}>No deposit accounts.</div>}
          </div>
        </div>
        <div style={{ ...panel, padding: 20 }}>
          {sectionT('Loans', `${loanList.length} active · ${fmtINR(loanOutstanding)} outstanding`)}
          <div className="mt-3 flex flex-col gap-4">
            {loanList.length === 0 ? (
              <div className="grid h-[160px] place-items-center text-[13px]" style={{ color: 'var(--text-3)' }}>No active loans.</div>
            ) : loanList.map((l) => {
              const sanctioned = Number(l.sanctioned_amount || l.disbursed_amount || 0);
              const out = Number(l.outstanding_principal || 0);
              const repaidPct = sanctioned > 0 ? Math.round(((sanctioned - out) / sanctioned) * 100) : 0;
              return (
                <div key={l.id} className="flex items-center gap-4">
                  <Ring value={repaidPct} label="repaid" />
                  <div className="min-w-0 flex-1">
                    <div className="num text-[13px] font-bold" style={{ color: 'var(--text)' }}>{l.loan_number}</div>
                    <div className="text-[12px]" style={{ color: 'var(--text-2)' }}>{l.product_name} · {l.interest_rate}% · {l.tenure_months}m</div>
                    <div className="mt-1.5 grid grid-cols-2 gap-2 text-[12px]">
                      <div><span style={{ color: 'var(--text-3)' }}>Sanctioned</span> <span className="num font-bold" style={{ color: 'var(--text)' }}>{fmtINR(sanctioned)}</span></div>
                      <div><span style={{ color: 'var(--text-3)' }}>Outstanding</span> <span className="num font-bold" style={{ color: 'var(--debit)' }}>{fmtINR(out)}</span></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Money flow table */}
      <Card>
        <CardHeader>
          <CardTitle><div className="flex items-center gap-2"><Wallet className="h-5 w-5" /> Money Flow (Ledger)</div></CardTitle>
          {moneyFlow && (
            <div className="text-right text-sm"><span className="text-gray-500 dark:text-gray-400">Net: </span>
              <span className={Number(moneyFlow.net_credit_minus_debit) >= 0 ? 'text-emerald-600' : 'text-red-600'}>{fmtINR(moneyFlow.net_credit_minus_debit)}</span></div>
          )}
        </CardHeader>
        <DataTable columns={flowColumns} data={moneyFlow?.rows ?? []} loading={flowLoading} emptyMessage="No ledger transactions for this member" />
      </Card>

      <Modal isOpen={showEdit} onClose={() => setShowEdit(false)} title="Edit Member">
        <MemberForm member={member} onSuccess={() => { setShowEdit(false); refresh(); }} onCancel={() => setShowEdit(false)} />
      </Modal>
    </div>
  );
}
