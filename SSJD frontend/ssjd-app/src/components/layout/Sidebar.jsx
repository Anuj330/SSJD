import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Users, UserCircle, Coins, PiggyBank, Landmark, CreditCard,
  Banknote, Receipt, ClipboardList, TrendingUp, BookOpen, FileText, BarChart3,
  Wallet, IdCard, MessageSquare, X,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { initials } from '../../utils/format';

const ADMIN_NAV = {
  MAIN: [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/members', icon: Users, label: 'Members' },
    { to: '/profiles', icon: UserCircle, label: 'Profiles' },
    { to: '/aadhaar', icon: IdCard, label: 'Aadhaar KYC' },
    { to: '/shares', icon: Coins, label: 'Share Money' },
    { to: '/deposits', icon: PiggyBank, label: 'Deposits' },
    { to: '/schemes', icon: Landmark, label: 'Schemes' },
    { to: '/loans', icon: CreditCard, label: 'Loans' },
    { to: '/loan-products', icon: Banknote, label: 'Loan Products' },
  ],
  'REPORTS & ADMIN': [
    { to: '/payments', icon: Receipt, label: 'Payments' },
    { to: '/messaging', icon: MessageSquare, label: 'SMS / WhatsApp' },
    { to: '/reports', icon: ClipboardList, label: 'Reports' },
    { to: '/analytics', icon: TrendingUp, label: 'Analytics' },
    { to: '/ledger/accounts', icon: BookOpen, label: 'Ledger' },
    { to: '/ledger/journal', icon: FileText, label: 'Journal Entry' },
    { to: '/ledger/trial-balance', icon: BarChart3, label: 'Trial Balance' },
    { to: '/ledger/statements', icon: Wallet, label: 'Statements' },
  ],
};

const MEMBER_NAV = {
  MAIN: [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/my-passbook', icon: Wallet, label: 'My Passbook' },
    { to: '/my-deposits', icon: PiggyBank, label: 'My Deposits' },
    { to: '/my-loans', icon: CreditCard, label: 'My Loans' },
    { to: '/my-shares', icon: Coins, label: 'My Shares' },
    { to: '/payments', icon: Receipt, label: 'Payments' },
  ],
};

export default function Sidebar({ open, onClose }) {
  const { role, sub } = useAuthStore();
  const groups = role === 'admin' ? ADMIN_NAV : MEMBER_NAV;

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-[rgba(8,14,24,.42)] lg:hidden" onClick={onClose} />}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[248px] flex-col transition-transform duration-200 lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}
      >
        {/* Brand */}
        <div className="flex items-center gap-3 px-[18px] pb-4 pt-5">
          <div className="flex h-[38px] w-[38px] flex-none items-center justify-center rounded-[11px]"
               style={{ background: 'linear-gradient(135deg,var(--navy),var(--navy-2))', boxShadow: 'var(--shadow)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21h18M5 21V10l7-5 7 5v11M9 21v-6h6v6" /></svg>
          </div>
          <div className="min-w-0">
            <div className="font-display text-[14.5px] font-bold leading-tight tracking-[.2px]" style={{ color: 'var(--text)' }}>SSJD</div>
            <div className="text-[11px] font-semibold tracking-[.4px]" style={{ color: 'var(--text-3)' }}>CO-OP SOCIETY</div>
          </div>
          <button onClick={onClose} className="ml-auto rounded-lg p-1 lg:hidden" style={{ color: 'var(--text-3)' }}><X className="h-5 w-5" /></button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 pb-4">
          {Object.entries(groups).map(([section, items]) => (
            <div key={section}>
              <div className="px-3 pb-1.5 pt-[18px] text-[10.5px] font-bold tracking-[.8px]" style={{ color: 'var(--text-3)' }}>{section}</div>
              <div className="flex flex-col gap-0.5">
                {items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.to === '/'}
                      onClick={onClose}
                      className="group flex items-center gap-3 rounded-[11px] px-3 py-2.5 text-[13.5px] font-semibold transition-colors"
                      style={({ isActive }) => ({
                        background: isActive ? 'var(--surface-2)' : 'transparent',
                        color: isActive ? 'var(--text)' : 'var(--text-2)',
                      })}
                    >
                      {({ isActive }) => (
                        <>
                          <Icon className="h-[18px] w-[18px] flex-none" style={{ color: isActive ? 'var(--accent)' : 'var(--text-3)' }} strokeWidth={1.7} />
                          <span className="flex-1">{item.label}</span>
                        </>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer: signed-in user */}
        <div className="p-3" style={{ borderTop: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2.5 rounded-[11px] px-3 py-2.5" style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
            <div className="flex h-9 w-9 flex-none items-center justify-center rounded-full font-display text-[13px] font-bold text-white" style={{ background: 'var(--blue)' }}>
              {initials(sub || (role === 'admin' ? 'Admin' : 'Member'))}
            </div>
            <div className="min-w-0">
              <div className="truncate text-[12.5px] font-bold" style={{ color: 'var(--text)' }}>{sub || (role === 'admin' ? 'Administrator' : 'Member')}</div>
              <div className="text-[11px]" style={{ color: 'var(--text-3)' }}>{role === 'admin' ? 'Administrator' : 'Member Portal'}</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
