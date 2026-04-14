import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, BookOpen, BarChart3, TrendingUp, ArrowRight, UserCircle, Wallet, Mail, Send } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../components/ui/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import { useAuthStore } from '../store/authStore';
import { membersService } from '../services/members';
import { ledgerService } from '../services/ledger';
import { profilesService } from '../services/profiles';
import { emailService } from '../services/email';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const { role, memberId } = useAuthStore();
  const isAdmin = role === 'admin';
  const [stats, setStats] = useState(null);
  const [trialBalance, setTrialBalance] = useState(null);
  const [moneyFlow, setMoneyFlow] = useState(null);
  const [profiles, setProfiles] = useState(null);
  const [emailMembers, setEmailMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [emailModal, setEmailModal] = useState(null); // null | { memberId, name } | 'bulk'
  const [emailSubject, setEmailSubject] = useState('');
  const [emailMessage, setEmailMessage] = useState('');
  const [sending, setSending] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchData() {
      try {
        if (isAdmin) {
          const [membersData, tbData, emailData] = await Promise.allSettled([
            membersService.list(),
            ledgerService.getTrialBalance(),
            emailService.listMembersWithEmail(),
          ]);
          if (membersData.status === 'fulfilled') setStats(membersData.value);
          if (tbData.status === 'fulfilled') setTrialBalance(tbData.value);
          if (emailData.status === 'fulfilled') setEmailMembers(emailData.value);
        } else {
          // Member: fetch own data
          const [flowData, profileData] = await Promise.allSettled([
            membersService.getMoneyFlow(memberId),
            profilesService.list(),
          ]);
          if (flowData.status === 'fulfilled') setMoneyFlow(flowData.value);
          if (profileData.status === 'fulfilled') setProfiles(profileData.value);
        }
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [isAdmin, memberId]);

  const handleSendEmail = async () => {
    if (!emailSubject.trim() || !emailMessage.trim()) {
      toast.error('Please enter subject and message');
      return;
    }
    setSending(true);
    try {
      if (emailModal === 'bulk') {
        const res = await emailService.sendBulk(emailSubject, emailMessage);
        toast.success(`Sent to ${res.sent} members${res.failed > 0 ? ` (${res.failed} failed)` : ''}`);
      } else {
        await emailService.send(emailModal.memberId, emailSubject, emailMessage);
        toast.success(`Email sent to ${emailModal.name}`);
      }
      setEmailModal(null);
      setEmailSubject('');
      setEmailMessage('');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send email');
    } finally {
      setSending(false);
    }
  };

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

  // ─── Admin Dashboard ───
  if (isAdmin) {
    const memberCount = stats?.count ?? 0;
    const accountCount = trialBalance?.rows?.length ?? 0;
    const totalDebit = trialBalance?.total_debit ?? 0;
    const totalCredit = trialBalance?.total_credit ?? 0;
    const isBalanced = trialBalance?.is_balanced ?? true;

    const statCards = [
      { label: 'Total Members', value: memberCount, icon: Users, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/30' },
      { label: 'Ledger Accounts', value: accountCount, icon: BookOpen, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/30' },
      { label: 'Total Debits', value: fmt(totalDebit), icon: TrendingUp, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/30' },
      { label: 'Total Credits', value: fmt(totalCredit), icon: BarChart3, color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-50 dark:bg-purple-900/30' },
    ];

    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Admin Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Overview of your cooperative society</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
            : statCards.map((stat) => {
                const Icon = stat.icon;
                return (
                  <Card key={stat.label} className="relative overflow-hidden">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.label}</p>
                        <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">{stat.value}</p>
                      </div>
                      <div className={`rounded-lg p-2.5 ${stat.bg}`}>
                        <Icon className={`h-5 w-5 ${stat.color}`} />
                      </div>
                    </div>
                  </Card>
                );
              })}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Trial Balance Status</CardTitle>
              {!loading && (
                <Badge color={isBalanced ? 'green' : 'red'}>
                  {isBalanced ? 'Balanced' : 'Unbalanced'}
                </Badge>
              )}
            </CardHeader>
            {loading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-5 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
                ))}
              </div>
            ) : trialBalance?.rows?.length ? (
              <div className="space-y-2">
                {trialBalance.rows.slice(0, 6).map((row) => (
                  <div key={row.account_id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50">
                    <div>
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{row.account_name}</span>
                      <span className="ml-2 text-xs text-gray-400">{row.account_code}</span>
                    </div>
                    <div className="text-right text-sm">
                      {Number(row.total_debit) > 0 && (
                        <span className="text-amber-600 dark:text-amber-400">Dr {fmt(row.total_debit)}</span>
                      )}
                      {Number(row.total_credit) > 0 && (
                        <span className="ml-3 text-emerald-600 dark:text-emerald-400">Cr {fmt(row.total_credit)}</span>
                      )}
                    </div>
                  </div>
                ))}
                {trialBalance.rows.length > 6 && (
                  <Button variant="ghost" size="sm" className="mt-2 w-full" onClick={() => navigate('/ledger/trial-balance')}>
                    View all {trialBalance.rows.length} accounts <ArrowRight className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">No ledger accounts yet.</p>
            )}
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                { label: 'Add Member', to: '/members', icon: Users },
                { label: 'New Account', to: '/ledger/accounts', icon: BookOpen },
                { label: 'Post Entry', to: '/ledger/journal', icon: BarChart3 },
                { label: 'View Profiles', to: '/profiles', icon: TrendingUp },
              ].map((action) => {
                const Icon = action.icon;
                return (
                  <button
                    key={action.label}
                    onClick={() => navigate(action.to)}
                    className="flex items-center gap-3 rounded-lg border border-gray-200 p-3 text-left transition-colors hover:border-primary-300 hover:bg-primary-50 dark:border-gray-700 dark:hover:border-primary-600 dark:hover:bg-primary-900/20"
                  >
                    <Icon className="h-5 w-5 text-gray-400" />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{action.label}</span>
                  </button>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Email Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Mail className="h-5 w-5" /> Email Notifications</CardTitle>
            <Button size="sm" onClick={() => { setEmailModal('bulk'); setEmailSubject(''); setEmailMessage(''); }}>
              <Send className="h-4 w-4" /> Send to All
            </Button>
          </CardHeader>
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-10 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
              ))}
            </div>
          ) : emailMembers.length === 0 ? (
            <p className="py-4 text-center text-sm text-gray-500">No members found.</p>
          ) : (
            <div className="space-y-1 max-h-80 overflow-y-auto">
              {emailMembers.map((m) => (
                <div key={m.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-xs font-bold text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">
                      {m.name?.charAt(0)?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {m.name} <span className="text-xs text-gray-400">#{m.id}</span>
                      </p>
                      <p className="text-xs text-gray-500">
                        {m.email || <span className="text-amber-500">No email</span>}
                        {m.phone && <span className="ml-2">{m.phone}</span>}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={!m.email}
                    title={m.email ? `Send email to ${m.name}` : 'No email address — update profile first'}
                    onClick={() => { setEmailModal({ memberId: m.id, name: m.name }); setEmailSubject(''); setEmailMessage(''); }}
                  >
                    <Mail className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Email Compose Modal */}
        {emailModal && (
          <Modal
            isOpen
            onClose={() => setEmailModal(null)}
            title={emailModal === 'bulk' ? 'Send Email to All Members' : `Send Email to ${emailModal.name}`}
            size="lg"
          >
            <div className="space-y-4">
              {emailModal === 'bulk' && (
                <p className="text-sm text-amber-600 dark:text-amber-400">
                  This will send the email to all members who have an email address on their profile.
                </p>
              )}
              <Input
                label="Subject"
                placeholder="Enter email subject"
                value={emailSubject}
                onChange={(e) => setEmailSubject(e.target.value)}
              />
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Message</label>
                <textarea
                  rows={6}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                  placeholder="Type your message here..."
                  value={emailMessage}
                  onChange={(e) => setEmailMessage(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setEmailModal(null)}>Cancel</Button>
                <Button
                  loading={sending}
                  disabled={!emailSubject.trim() || !emailMessage.trim()}
                  onClick={handleSendEmail}
                >
                  <Send className="h-4 w-4" /> {emailModal === 'bulk' ? 'Send to All' : 'Send Email'}
                </Button>
              </div>
            </div>
          </Modal>
        )}
      </div>
    );
  }

  // ─── Member Dashboard ───
  const hasProfile = Array.isArray(profiles) && profiles.length > 0;
  const totalDr = moneyFlow?.total_debit ?? 0;
  const totalCr = moneyFlow?.total_credit ?? 0;
  const net = moneyFlow?.net_credit_minus_debit ?? 0;

  const memberStats = [
    { label: 'Total Debits', value: fmt(totalDr), icon: TrendingUp, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/30' },
    { label: 'Total Credits', value: fmt(totalCr), icon: BarChart3, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/30' },
    { label: 'Net Balance', value: fmt(net), icon: Wallet, color: Number(net) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400', bg: Number(net) >= 0 ? 'bg-emerald-50 dark:bg-emerald-900/30' : 'bg-red-50 dark:bg-red-900/30' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">My Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Your personal account overview</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)
          : memberStats.map((stat) => {
              const Icon = stat.icon;
              return (
                <Card key={stat.label}>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.label}</p>
                      <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">{stat.value}</p>
                    </div>
                    <div className={`rounded-lg p-2.5 ${stat.bg}`}>
                      <Icon className={`h-5 w-5 ${stat.color}`} />
                    </div>
                  </div>
                </Card>
              );
            })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { label: hasProfile ? 'View My Profile' : 'Create My Profile', to: '/profiles', icon: UserCircle },
            { label: 'My Passbook', to: '/my-passbook', icon: Wallet },
            { label: 'My Deposits', to: '/my-deposits', icon: Users },
            { label: 'My Loans', to: '/my-loans', icon: BarChart3 },
            { label: 'My Shares', to: '/my-shares', icon: TrendingUp },
          ].map(action => {
            const Icon = action.icon;
            return (
              <button key={action.label} onClick={() => navigate(action.to)}
                className="flex items-center gap-3 rounded-lg border border-gray-200 p-3 text-left transition-colors hover:border-primary-300 hover:bg-primary-50 dark:border-gray-700 dark:hover:border-primary-600 dark:hover:bg-primary-900/20">
                <Icon className="h-5 w-5 text-gray-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{action.label}</span>
              </button>
            );
          })}
        </div>
      </Card>

      {moneyFlow?.rows?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
          </CardHeader>
          <div className="space-y-2">
            {moneyFlow.rows.slice(0, 5).map((row, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50">
                <div>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{row.txn_type}</span>
                  <span className="ml-2 text-xs text-gray-400">{row.txn_ref}</span>
                </div>
                <div className="text-sm">
                  {Number(row.dr_amount) > 0 && <span className="text-amber-600 dark:text-amber-400">Dr {fmt(row.dr_amount)}</span>}
                  {Number(row.cr_amount) > 0 && <span className="text-emerald-600 dark:text-emerald-400">Cr {fmt(row.cr_amount)}</span>}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
