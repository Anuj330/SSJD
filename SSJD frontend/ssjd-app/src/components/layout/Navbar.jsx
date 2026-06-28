import { Menu, Moon, Sun, LogOut, Search, Bell } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useThemeStore } from '../../store/themeStore';
import { useAuthStore } from '../../store/authStore';
import { initials } from '../../utils/format';

const TITLES = [
  ['/members', 'Members', 'Manage member accounts & KYC'],
  ['/profiles', 'Profiles', 'Member profiles & details'],
  ['/aadhaar', 'Aadhaar KYC', 'Upload & map Aadhaar cards to members'],
  ['/shares', 'Share Money', 'Monthly contributions & balances'],
  ['/deposits', 'Deposits', 'FD / RD deposit accounts'],
  ['/schemes', 'Schemes', 'Deposit & savings schemes'],
  ['/loan-products', 'Loan Products', 'Configure loan offerings'],
  ['/loans', 'Loans', 'Disbursements & repayments'],
  ['/payments', 'Payments', 'Payment history & receipts'],
  ['/messaging', 'SMS / WhatsApp', 'Send messages to members'],
  ['/reports', 'Reports', 'Financial statements'],
  ['/analytics', 'Analytics', 'KPIs & dividends'],
  ['/ledger/accounts', 'Ledger Accounts', 'Chart of accounts'],
  ['/ledger/journal', 'Journal Entry', 'Post double-entry transactions'],
  ['/ledger/trial-balance', 'Trial Balance', 'Account balances'],
  ['/ledger/statements', 'Statements', 'Account statements'],
  ['/my-passbook', 'My Passbook', 'Your transaction history'],
  ['/my-deposits', 'My Deposits', 'Your deposit accounts'],
  ['/my-loans', 'My Loans', 'Your loans & EMIs'],
  ['/my-shares', 'My Share Money', 'Your contributions & balance'],
];

function titleFor(pathname, role) {
  if (pathname === '/') return role === 'admin'
    ? ['Dashboard', "Overview of your society's finances"]
    : ['My Dashboard', 'Your account at a glance'];
  const hit = TITLES.find(([p]) => pathname === p || pathname.startsWith(p + '/'));
  return hit ? [hit[1], hit[2]] : ['SSJD', 'Cooperative Society'];
}

export default function Navbar({ onMenuClick }) {
  const { theme, toggleTheme } = useThemeStore();
  const { logout, role, sub } = useAuthStore();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [title, subtitle] = titleFor(pathname, role);
  const dark = theme === 'dark';

  const sq = { background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-2)' };

  return (
    <header
      className="sticky top-0 z-30 flex h-16 items-center gap-3 px-4 lg:px-6"
      style={{ background: 'color-mix(in srgb, var(--bg) 80%, transparent)', backdropFilter: 'blur(12px)', borderBottom: '1px solid var(--border)' }}
    >
      <button onClick={onMenuClick} className="flex h-[38px] w-[38px] flex-none items-center justify-center rounded-[10px] lg:hidden" style={sq}>
        <Menu className="h-[18px] w-[18px]" />
      </button>

      <div className="min-w-0">
        <h1 className="font-display truncate text-[20px] font-bold tracking-[-.2px]" style={{ color: 'var(--text)' }}>{title}</h1>
        <div className="truncate text-[12.5px]" style={{ color: 'var(--text-2)' }}>{subtitle}</div>
      </div>

      <div className="flex-1" />

      <div className="relative hidden w-[280px] max-w-[34vw] sm:block">
        <Search className="absolute left-[13px] top-1/2 h-4 w-4 -translate-y-1/2" style={{ color: 'var(--text-3)' }} />
        <input
          placeholder="Search members, txns…"
          className="w-full rounded-[10px] py-[9px] pl-9 pr-3 text-[13px] outline-none"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
        />
      </div>

      <button onClick={toggleTheme} title="Toggle theme" className="flex h-[38px] w-[38px] flex-none items-center justify-center rounded-[10px]" style={sq}>
        {dark ? <Sun className="h-[17px] w-[17px]" style={{ color: 'var(--amber)' }} /> : <Moon className="h-[17px] w-[17px]" />}
      </button>

      <button title="Notifications" className="relative flex h-[38px] w-[38px] flex-none items-center justify-center rounded-[10px]" style={sq}>
        <Bell className="h-[17px] w-[17px]" />
        <span className="absolute right-2 top-[7px] h-2 w-2 rounded-full" style={{ background: 'var(--debit)', border: '2px solid var(--surface)' }} />
      </button>

      <button onClick={() => { logout(); navigate('/login'); }} title="Logout" className="flex h-[38px] w-[38px] flex-none items-center justify-center rounded-[10px]" style={sq}>
        <LogOut className="h-[17px] w-[17px]" />
      </button>

      <div className="flex h-9 w-9 items-center justify-center rounded-full font-display text-[13px] font-bold text-white" style={{ background: 'var(--blue)' }}>
        {initials(sub || (role === 'admin' ? 'Admin' : 'Member'))}
      </div>
    </header>
  );
}
