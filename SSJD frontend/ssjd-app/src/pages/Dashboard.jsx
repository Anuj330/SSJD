import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, Coins, CreditCard, PiggyBank, AlertTriangle, Plus, ArrowUpRight, ArrowDownRight,
  ArrowDownLeft, Wallet, TrendingUp, Landmark,
} from 'lucide-react';
import { AreaLine, Bars } from '../components/charts/Charts';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { useAuthStore } from '../store/authStore';
import { useRazorpay } from '../hooks/useRazorpay';
import { membersService } from '../services/members';
import { reportsService } from '../services/reports';
import { sharesService } from '../services/shares';
import { loansService } from '../services/loans';
import { fmtINR, fmtCompact, fmtNum, initials, avatarColor } from '../utils/format';

const CARD = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 16, boxShadow: 'var(--shadow)' };
const fmtDate = (d) => (d ? new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : '');
const fmtDateTime = (d) => (d ? new Date(d).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '');
const fmtDateFull = (d) => (d ? new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '');
const TYPE_LABEL = { monthly_share_deposit: 'Share deposit', withdrawal: 'Withdrawal', dividend: 'Dividend' };

export default function Dashboard() {
  const { role, memberId, sub } = useAuthStore();
  const isAdmin = role === 'admin';
  const [kpis, setKpis] = useState(null);
  const [ov, setOv] = useState(null);
  const [moneyFlow, setMoneyFlow] = useState(null);
  const [memberShares, setMemberShares] = useState(null);
  const [memberLoans, setMemberLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [layout, setLayout] = useState('overview');
  const [payOpen, setPayOpen] = useState(false);
  const [payAmount, setPayAmount] = useState('');
  const navigate = useNavigate();
  const { pay, loading: paying } = useRazorpay();

  const doPay = () => {
    const amt = Math.floor(Number(payAmount) || 0);
    if (amt <= 0) return;
    pay('share_purchase', memberId, amt, () => {
      setPayOpen(false); setPayAmount('');
      sharesService.getMemberShares(memberId).then(setMemberShares).catch(() => {});
    });
  };

  useEffect(() => {
    (async () => {
      try {
        if (isAdmin) {
          const [k, o] = await Promise.allSettled([reportsService.dashboardKPIs(), reportsService.dashboardOverview()]);
          if (k.status === 'fulfilled') setKpis(k.value);
          if (o.status === 'fulfilled') setOv(o.value);
        } else {
          const [f, sh, ln] = await Promise.allSettled([membersService.getMoneyFlow(memberId), sharesService.getMemberShares(memberId), loansService.list()]);
          if (f.status === 'fulfilled') setMoneyFlow(f.value);
          if (sh.status === 'fulfilled') setMemberShares(sh.value);
          if (ln.status === 'fulfilled') setMemberLoans(Array.isArray(ln.value) ? ln.value : []);
        }
      } finally { setLoading(false); }
    })();
  }, [isAdmin, memberId]);

  // ═══════════════ ADMIN ═══════════════
  if (isAdmin) {
    const k = kpis || {};
    const stats = [
      { label: 'Total Members', value: fmtNum(k.total_members ?? 0), icon: Users, delta: `${fmtNum(k.recent_transactions_30d ?? 0)} txns / 30d` },
      { label: 'Share Money', value: fmtCompact(k.total_share_capital ?? 0), icon: Coins, delta: `${fmtNum(k.active_schemes ?? 0)} schemes` },
      { label: 'Active Loans', value: fmtNum(k.active_loans ?? 0), icon: CreditCard, delta: `${fmtCompact(k.total_loan_outstanding ?? 0)} out` },
      { label: 'Deposits', value: fmtCompact(k.total_deposit_balance ?? 0), icon: PiggyBank, delta: `${fmtNum(k.active_deposits ?? 0)} active` },
      { label: 'Overdue EMIs', value: fmtNum(k.overdue_emis ?? 0), icon: AlertTriangle, delta: (k.overdue_emis ?? 0) ? 'needs follow-up' : 'all on track' },
    ];
    const growth = (ov?.member_growth ?? []).map((g) => ({ label: g.month.slice(2), value: g.total }));
    const coll = (ov?.monthly_collections ?? []).map((c) => ({ label: c.month.slice(2), value: Math.round(c.amount / 1000) }));
    const recent = ov?.recent_transactions ?? [];
    const members = ov?.recent_members ?? [];

    const pill = (id, text) => (
      <button onClick={() => setLayout(id)} className="rounded-[9px] px-3.5 py-1.5 text-[13px] font-bold" style={{
        background: layout === id ? 'var(--surface)' : 'transparent',
        color: layout === id ? 'var(--text)' : 'var(--text-2)',
        boxShadow: layout === id ? 'var(--shadow)' : 'none',
      }}>{text}</button>
    );
    const sectionTitle = (t, s) => (<div><div className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>{t}</div><div className="text-[12px]" style={{ color: 'var(--text-2)' }}>{s}</div></div>);

    return (
      <div className="animate-fade-up">
        <div className="mb-5 flex flex-wrap items-center gap-3.5">
          <div className="inline-flex gap-[3px] rounded-[11px] p-1" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
            {pill('overview', 'Overview')}{pill('analytics', 'Analytics')}{pill('operations', 'Operations')}
          </div>
          <div className="flex-1" />
          <button onClick={() => navigate('/shares')} className="inline-flex items-center gap-1.5 rounded-[10px] px-4 py-2.5 text-[13px] font-bold text-white" style={{ background: 'var(--accent)', boxShadow: 'var(--shadow)' }}>
            <Plus className="h-4 w-4" strokeWidth={2.2} /> New Transaction
          </button>
        </div>

        {/* KPI cards */}
        <div className="mb-[18px] grid gap-3.5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))' }}>
          {stats.map((c) => {
            const Icon = c.icon;
            return (
              <div key={c.label} style={{ ...CARD, padding: '16px 16px 14px' }}>
                <div className="flex h-[34px] w-[34px] items-center justify-center rounded-[9px]" style={{ background: 'var(--surface-2)' }}>
                  <Icon className="h-[17px] w-[17px]" style={{ color: 'var(--text-2)' }} strokeWidth={1.7} />
                </div>
                <div className="mt-3 text-[12.5px] font-semibold" style={{ color: 'var(--text-2)' }}>{c.label}</div>
                <div className="num mt-0.5 text-[23px] font-bold" style={{ color: 'var(--text)' }}>{loading ? '—' : c.value}</div>
                <div className="mt-0.5 text-[12px] font-semibold" style={{ color: 'var(--text-3)' }}>{c.delta}</div>
              </div>
            );
          })}
        </div>

        {/* Layout-specific */}
        {layout === 'overview' && (
          <div className="mb-4 grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(320px,1fr))' }}>
            <div style={{ ...CARD, padding: 20 }}>
              <div className="mb-1.5 flex items-center justify-between">{sectionTitle('Member Growth', 'Cumulative members by join month')}
                <span className="rounded-[7px] px-2 py-1 text-[12px] font-bold" style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }}>{fmtNum(k.total_members ?? 0)} total</span></div>
              <AreaLine data={growth} />
            </div>
            <div style={{ ...CARD, padding: 20 }}>
              {sectionTitle('Monthly Collections', '₹ in thousands · share money')}
              <div className="mt-2"><Bars data={coll} /></div>
            </div>
          </div>
        )}
        {layout === 'analytics' && (
          <div className="mb-4 grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(320px,1fr))' }}>
            <div style={{ ...CARD, padding: 20 }}>{sectionTitle('Monthly Collections', '₹ in thousands · last months')}<div className="mt-2"><Bars data={coll} height={240} /></div></div>
            <div style={{ ...CARD, padding: 20 }}>{sectionTitle('Member Growth', 'Cumulative members')}<div className="mt-2"><AreaLine data={growth} height={240} /></div></div>
          </div>
        )}
        {layout === 'operations' && (
          <div className="mb-4" style={{ ...CARD, padding: 20 }}>
            <div className="mb-3 flex items-center gap-2.5 text-[15px] font-bold" style={{ color: 'var(--text)' }}>
              Operations Focus
              {(k.overdue_emis ?? 0) > 0 && <span className="rounded-[6px] px-2 py-0.5 text-[11px] font-bold" style={{ background: 'var(--amber-soft)', color: 'var(--amber)' }}>{fmtNum(k.overdue_emis)} overdue</span>}
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {[['Overdue EMIs', fmtNum(k.overdue_emis ?? 0), 'var(--debit)'], ['Loan Outstanding', fmtCompact(k.total_loan_outstanding ?? 0), 'var(--text)'], ['Active Loans', fmtNum(k.active_loans ?? 0), 'var(--text)']].map(([l, v, color]) => (
                <div key={l} className="rounded-xl p-4" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
                  <div className="text-[12px] font-semibold" style={{ color: 'var(--text-2)' }}>{l}</div>
                  <div className="num mt-1 text-[22px] font-bold" style={{ color }}>{v}</div>
                </div>
              ))}
            </div>
            <button onClick={() => navigate('/loans')} className="mt-4 rounded-[10px] px-4 py-2.5 text-[13px] font-bold text-white" style={{ background: 'var(--accent)' }}>Review loans</button>
          </div>
        )}

        {/* Recent transactions + member activity */}
        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(320px,1fr))' }}>
          <div style={{ ...CARD, overflow: 'hidden' }}>
            <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: '1px solid var(--border)' }}>
              <div className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>Recent Transactions</div>
              <button onClick={() => navigate('/shares')} className="text-[12.5px] font-bold" style={{ color: 'var(--accent)' }}>View all</button>
            </div>
            <div className="px-2 py-1.5">
              {recent.length === 0 ? <div className="px-3 py-6 text-center text-[13px]" style={{ color: 'var(--text-3)' }}>No transactions yet.</div> :
                recent.map((t, i) => (
                  <div key={i} className="flex items-center gap-3 rounded-[10px] px-3 py-2.5">
                    <div className="flex h-[34px] w-[34px] flex-none items-center justify-center rounded-[9px] font-display text-[12px] font-bold text-white" style={{ background: avatarColor(t.name) }}>{initials(t.name)}</div>
                    <div className="min-w-0 flex-1"><div className="text-[13.5px] font-semibold" style={{ color: 'var(--text)' }}>{t.name}</div><div className="text-[12px]" style={{ color: 'var(--text-2)' }}>{TYPE_LABEL[t.txn_type] || t.txn_type} · {fmtDate(t.txn_date)}</div></div>
                    <div className="num w-24 text-right font-bold" style={{ color: t.txn_type === 'withdrawal' ? 'var(--debit)' : 'var(--accent)' }}>{t.txn_type === 'withdrawal' ? '−' : '+'}{fmtINR(t.amount)}</div>
                  </div>
                ))}
            </div>
          </div>
          <div style={{ ...CARD, overflow: 'hidden' }}>
            <div className="px-5 py-4 text-[15px] font-bold" style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)' }}>Recent Members</div>
            <div className="px-2 py-2">
              {members.length === 0 ? <div className="px-3 py-6 text-center text-[13px]" style={{ color: 'var(--text-3)' }}>No members yet.</div> :
                members.map((m, i) => (
                  <div key={i} className="flex items-center gap-3 px-3 py-2.5">
                    <div className="flex h-[30px] w-[30px] flex-none items-center justify-center rounded-full font-display text-[11px] font-bold text-white" style={{ background: avatarColor(m.name || String(m.acno)) }}>{initials(m.name || '?')}</div>
                    <div className="min-w-0 flex-1 text-[13px]" style={{ color: 'var(--text-2)' }}>
                      <span className="font-bold" style={{ color: 'var(--text)' }}>{m.name}</span> joined
                      <div className="num mt-0.5 text-[11px]" style={{ color: 'var(--text-3)' }}>Acc #{m.acno}</div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ═══════════════ MEMBER ═══════════════
  const totalDr = Number(moneyFlow?.total_debit ?? 0);
  const totalCr = Number(moneyFlow?.total_credit ?? 0);
  const shareBalance = Number(memberShares?.balance ?? 0);
  const loanOutstanding = (Array.isArray(memberLoans) ? memberLoans : [])
    .reduce((sum, l) => sum + Number(l.outstanding_principal ?? 0), 0);
  const shareTxns = Array.isArray(memberShares?.transactions) ? memberShares.transactions : [];
  const flowRows = Array.isArray(moneyFlow?.rows) ? moneyFlow.rows : [];
  const sIsDebit = (t) => String(t).toLowerCase() === 'withdrawal';
  const byDateDesc = (a, b) => new Date(b.date) - new Date(a.date);
  // Online payments carry an exact timestamp → show date + time. Everything else
  // (manual/legacy entries) shows the transaction date; created_at may be the
  // import time so we don't show a misleading clock time for those.
  const shareWhen = (t) =>
    t.remarks === 'Online payment' && t.created_at ? fmtDateTime(t.created_at) : fmtDateFull(t.txn_date);
  const shareActivity = shareTxns
    .map((t) => ({ date: t.created_at || t.txn_date, when: shareWhen(t), label: TYPE_LABEL[t.txn_type] || t.txn_type, ref: 'Share Money', amount: Number(t.amount), cr: !sIsDebit(t.txn_type) }))
    .sort(byDateDesc).slice(0, 8);
  const loanActivity = flowRows
    .map((r) => ({ date: r.created_at, when: fmtDateTime(r.created_at), label: String(r.txn_type || '').replace(/_/g, ' '), ref: r.txn_ref, amount: Number(r.cr_amount) > 0 ? Number(r.cr_amount) : Number(r.dr_amount), cr: Number(r.cr_amount) > 0 }))
    .sort(byDateDesc).slice(0, 8);

  return (
    <div className="animate-fade-up space-y-5">
      <div className="relative overflow-hidden rounded-3xl text-white shadow-xl"
           style={{ background: 'radial-gradient(130% 120% at 100% 0%, rgba(11,163,113,.45), transparent 50%), radial-gradient(120% 120% at 0% 100%, rgba(47,111,237,.20), transparent 55%), linear-gradient(150deg,#16243A,#0E1A2B 58%,#091320)' }}>
        {/* top hairline highlight */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px" style={{ background: 'linear-gradient(90deg, transparent, rgba(255,255,255,.18), transparent)' }} />
        {/* decorative concentric rings on the right */}
        <div className="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full" style={{ border: '1px solid rgba(255,255,255,.06)' }} />
        <div className="pointer-events-none absolute -right-6 -top-10 h-44 w-44 rounded-full" style={{ border: '1px solid rgba(255,255,255,.05)' }} />

        <div className="relative grid gap-6 p-6 sm:p-7 lg:grid-cols-[1.4fr_1fr] lg:items-end">
          {/* Left: brand, balance, CTA */}
          <div>
            <div className="flex items-center gap-3">
              {/* EMV-style chip */}
              <div className="relative h-8 w-11 overflow-hidden rounded-[7px]" style={{ background: 'linear-gradient(135deg,#F4D67A,#C79A3B)' }}>
                <div className="absolute inset-x-1.5 top-1/2 h-px -translate-y-1/2" style={{ background: 'rgba(0,0,0,.25)' }} />
                <div className="absolute inset-y-1.5 left-1/2 w-px -translate-x-1/2" style={{ background: 'rgba(0,0,0,.25)' }} />
              </div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.16em]" style={{ color: 'rgba(255,255,255,.65)' }}>SSJD Member Card</div>
            </div>

            <div className="mt-6 text-[11px] font-semibold uppercase tracking-[0.16em]" style={{ color: 'rgba(255,255,255,.55)' }}>Share Money Balance</div>
            <div className="num mt-1 text-[42px] font-bold leading-none">{loading ? '—' : fmtINR(shareBalance)}</div>
            <div className="mt-2.5 flex flex-wrap items-center gap-2">
              <span className="num inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12.5px] font-semibold"
                    style={{ background: 'rgba(11,163,113,.16)', color: '#7BE6BE', border: '1px solid rgba(11,163,113,.32)' }}>
                <Coins className="h-3.5 w-3.5" /> Share {fmtCompact(shareBalance)}
              </span>
              <span className="num inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12.5px] font-semibold"
                    style={{ background: 'rgba(47,111,237,.16)', color: '#9DBCFF', border: '1px solid rgba(47,111,237,.32)' }}>
                <CreditCard className="h-3.5 w-3.5" /> Loan {fmtCompact(loanOutstanding)}
              </span>
            </div>

            <div className="mt-6">
              <button onClick={() => setPayOpen(true)}
                className="inline-flex items-center gap-2 rounded-[11px] px-5 py-3 text-[14px] font-bold transition-transform hover:-translate-y-0.5"
                style={{ background: 'var(--accent)', color: '#04130D', boxShadow: '0 8px 20px rgba(11,163,113,.35)' }}>
                <Plus className="h-[18px] w-[18px]" strokeWidth={2.6} /> Pay Share Money
              </button>
            </div>
          </div>

          {/* Right: card meta */}
          <div className="flex flex-col gap-4 lg:items-end lg:text-right">
            <span className="num self-start rounded-full px-3 py-1 text-[12px] font-semibold lg:self-end"
                  style={{ background: 'rgba(255,255,255,.1)', border: '1px solid rgba(255,255,255,.16)' }}>
              {sub || `MBR-${memberId ?? '----'}`}
            </span>
            <div className="hidden gap-8 lg:flex">
              <div>
                <div className="text-[10px] uppercase tracking-[0.14em]" style={{ color: 'rgba(255,255,255,.45)' }}>Member ID</div>
                <div className="num mt-1 text-[15px] font-semibold">{memberId ?? '—'}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.14em]" style={{ color: 'rgba(255,255,255,.45)' }}>Account</div>
                <div className="mt-1 text-[15px] font-semibold">Share Savings</div>
              </div>
            </div>
          </div>
        </div>

        <div className="pointer-events-none absolute -bottom-7 right-3 font-display text-[120px] font-extrabold leading-none text-white/[0.045] select-none">SSJD</div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { l: 'Share Money', sub: 'Your savings balance', v: fmtCompact(shareBalance), Icon: Coins, fg: 'var(--accent)', bg: 'var(--accent-soft)' },
          { l: 'Received', sub: 'Money credited to you', v: fmtCompact(totalCr), Icon: ArrowDownLeft, fg: 'var(--accent)', bg: 'var(--accent-soft)' },
          { l: 'Paid / Disbursed', sub: 'Money debited from you', v: fmtCompact(totalDr), Icon: ArrowUpRight, fg: 'var(--debit)', bg: 'var(--amber-soft)' },
        ].map(({ l, sub, v, Icon, fg, bg }) => (
          <div key={l} style={{ ...CARD, padding: 18 }}>
            <div className="flex h-9 w-9 items-center justify-center rounded-[9px]" style={{ background: bg }}><Icon className="h-[18px] w-[18px]" style={{ color: fg }} /></div>
            <div className="mt-3 text-[12.5px] font-semibold" style={{ color: 'var(--text-2)' }}>{l}</div>
            <div className="num mt-0.5 text-[22px] font-bold" style={{ color: 'var(--text)' }}>{loading ? '—' : v}</div>
            <div className="mt-0.5 text-[11px]" style={{ color: 'var(--text-3)' }}>{sub}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(320px,1fr))' }}>
        <ActivityCard title="Share Money" items={shareActivity} onView={() => navigate('/my-shares')} viewLabel="My Shares" empty="No share deposits yet." />
        <ActivityCard title="Loans & Other" items={loanActivity} onView={() => navigate('/my-passbook')} viewLabel="Passbook" empty="No loan activity yet." />
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[['My Passbook', '/my-passbook', Wallet], ['My Deposits', '/my-deposits', PiggyBank], ['My Loans', '/my-loans', CreditCard], ['My Shares', '/my-shares', Coins], ['Payments', '/payments', Landmark], ['Schemes', '/schemes', TrendingUp]].map(([l, to, Icon]) => (
          <button key={l} onClick={() => navigate(to)} className="flex items-center gap-3 rounded-xl p-3 text-left" style={{ ...CARD }}>
            <span className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: 'var(--surface-2)', color: 'var(--text-2)' }}><Icon className="h-[18px] w-[18px]" /></span>
            <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{l}</span>
          </button>
        ))}
      </div>

      <Modal isOpen={payOpen} onClose={() => setPayOpen(false)} title="Pay Share Money" size="md">
        <div className="space-y-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Add your monthly share contribution — paid securely via Razorpay.</p>
          <Input label="Amount (₹)" type="number" min="1" step="1" placeholder="500" value={payAmount} onChange={(e) => setPayAmount(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setPayOpen(false)}>Cancel</Button>
            <Button loading={paying} disabled={!(Number(payAmount) > 0)} onClick={doPay}>
              Pay {Number(payAmount) > 0 ? fmtINR(Math.floor(Number(payAmount))) : ''}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function ActivityCard({ title, items, onView, viewLabel, empty }) {
  return (
    <div style={{ ...CARD, overflow: 'hidden' }}>
      <div className="flex items-center justify-between px-5 py-4 text-[15px] font-bold" style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)' }}>
        {title}
        <button onClick={onView} className="text-[12.5px] font-bold" style={{ color: 'var(--accent)' }}>{viewLabel}</button>
      </div>
      <div className="px-2 py-2">
        {items.length === 0 ? <div className="px-3 py-6 text-center text-[13px]" style={{ color: 'var(--text-3)' }}>{empty}</div> :
          items.map((r, i) => (
            <div key={i} className="flex items-center gap-3 rounded-[10px] px-3 py-2.5">
              <div className="flex h-9 w-9 flex-none items-center justify-center rounded-[9px]" style={{ background: r.cr ? 'var(--accent-soft)' : 'var(--amber-soft)', color: r.cr ? 'var(--accent)' : 'var(--amber)' }}>{r.cr ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}</div>
              <div className="min-w-0 flex-1"><div className="text-[13.5px] font-semibold capitalize" style={{ color: 'var(--text)' }}>{r.label}</div><div className="num text-[11px]" style={{ color: 'var(--text-3)' }}>{r.when}{r.ref && r.ref !== 'Share Money' ? ` · ${r.ref}` : ''}</div></div>
              <div className="num font-bold" style={{ color: r.cr ? 'var(--accent)' : 'var(--debit)' }}>{r.cr ? '+' : '−'}{fmtINR(r.amount)}</div>
            </div>
          ))}
      </div>
    </div>
  );
}
