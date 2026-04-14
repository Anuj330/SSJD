import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  UserCircle,
  BookOpen,
  FileText,
  BarChart3,
  Wallet,
  Landmark,
  PiggyBank,
  Banknote,
  CreditCard,
  Coins,
  ClipboardList,
  TrendingUp,
  Receipt,
  X,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

const allNavItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', roles: ['admin', 'member'] },
  { to: '/members', icon: Users, label: 'Members', roles: ['admin'] },
  { to: '/profiles', icon: UserCircle, label: 'Profiles', roles: ['admin', 'member'] },
  { heading: 'Deposits', roles: ['admin', 'member'] },
  { to: '/schemes', icon: Landmark, label: 'Schemes', roles: ['admin', 'member'] },
  { to: '/deposits', icon: PiggyBank, label: 'Deposit Accounts', roles: ['admin'] },
  { to: '/my-deposits', icon: PiggyBank, label: 'My Deposits', roles: ['member'] },
  { to: '/my-passbook', icon: Wallet, label: 'My Passbook', roles: ['member'] },
  { heading: 'Loans', roles: ['admin', 'member'] },
  { to: '/loan-products', icon: Banknote, label: 'Loan Products', roles: ['admin'] },
  { to: '/loans', icon: CreditCard, label: 'Loans', roles: ['admin'] },
  { to: '/my-loans', icon: CreditCard, label: 'My Loans', roles: ['member'] },
  { heading: 'Capital', roles: ['admin', 'member'] },
  { to: '/shares', icon: Coins, label: 'Share Capital', roles: ['admin'] },
  { to: '/my-shares', icon: Coins, label: 'My Shares', roles: ['member'] },
  { heading: 'Payments', roles: ['admin', 'member'] },
  { to: '/payments', icon: Receipt, label: 'Payment History', roles: ['admin', 'member'] },
  { heading: 'Reports', roles: ['admin'] },
  { to: '/reports', icon: ClipboardList, label: 'Reports', roles: ['admin'] },
  { to: '/analytics', icon: TrendingUp, label: 'Analytics', roles: ['admin'] },
  { heading: 'Ledger', roles: ['admin'] },
  { to: '/ledger/accounts', icon: BookOpen, label: 'Accounts', roles: ['admin'] },
  { to: '/ledger/journal', icon: FileText, label: 'Journal Entry', roles: ['admin'] },
  { to: '/ledger/trial-balance', icon: BarChart3, label: 'Trial Balance', roles: ['admin'] },
  { to: '/ledger/statements', icon: Wallet, label: 'Statements', roles: ['admin'] },
];

export default function Sidebar({ open, onClose }) {
  const { role } = useAuthStore();

  const navItems = allNavItems.filter((item) => item.roles.includes(role));

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-gray-200 bg-white transition-transform duration-200 dark:border-gray-800 dark:bg-gray-950 lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-6 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-sm font-bold text-white">
              S
            </div>
            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              SSJD
            </span>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 lg:hidden dark:hover:bg-gray-800">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-1">
            {navItems.map((item, i) => {
              if (item.heading) {
                return (
                  <li key={i} className="px-3 pb-1 pt-5">
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                      {item.heading}
                    </span>
                  </li>
                );
              }
              const Icon = item.icon;
              return (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === '/'}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200'
                      }`
                    }
                  >
                    <Icon className="h-5 w-5 shrink-0" />
                    {item.label}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="border-t border-gray-200 px-4 py-3 dark:border-gray-800">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Shramik Sahkari Jaivik Darshan
          </p>
        </div>
      </aside>
    </>
  );
}
