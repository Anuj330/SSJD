import React from 'react';
import { LayoutDashboard, FileText, CreditCard, LogOut, X, Menu } from 'lucide-react';

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  currentPage: string;
  setCurrentPage: (page: string) => void;
  onLogout: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  sidebarOpen,
  setSidebarOpen,
  currentPage,
  setCurrentPage,
  onLogout
}) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'balance', label: 'Balance Statement', icon: FileText },
    { id: 'loan', label: 'Loan Statement', icon: CreditCard }
  ];

  return (
    <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gradient-to-b from-blue-800 to-blue-900 text-white transition-all duration-300 fixed h-full z-20`}>
      <div className="p-4 flex items-center justify-between border-b border-blue-700">
        {sidebarOpen && <h2 className="text-xl font-bold">SSID Panel</h2>}
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 hover:bg-blue-700 rounded-lg">
          {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      <nav className="mt-6">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full flex items-center ${sidebarOpen ? 'px-6' : 'px-4 justify-center'} py-4 hover:bg-blue-700 transition ${
                currentPage === item.id ? 'bg-blue-700 border-l-4 border-white' : ''
              }`}
            >
              <Icon className="w-5 h-5" />
              {sidebarOpen && <span className="ml-3 font-medium">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      <div className="absolute bottom-0 w-full border-t border-blue-700">
        <button
          onClick={onLogout}
          className={`w-full flex items-center ${sidebarOpen ? 'px-6' : 'px-4 justify-center'} py-4 hover:bg-red-600 transition`}
        >
          <LogOut className="w-5 h-5" />
          {sidebarOpen && <span className="ml-3 font-medium">Logout</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;