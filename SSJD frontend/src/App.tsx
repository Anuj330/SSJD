import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import Dashboard from './components/dashboard/Dashboard';
import BalanceStatement from './components/statements/BalanceStatement';
import LoanStatement from './components/statements/LoanStatement';
import { LayoutDashboard, FileText, CreditCard, LogOut, X, Menu } from 'lucide-react';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode; isAuthenticated: boolean }> = ({ 
  children, 
  isAuthenticated 
}) => {
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Main App Component with Router
const AppContent: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userName] = useState('ANUJ MAHTO');
  const [memberId] = useState('12345');
  const navigate = useNavigate();

  const handleLogin = (username: string, password: string) => {
    if (username && password) {
      setIsAuthenticated(true);
      navigate('/dashboard');
    } else {
      alert('Please enter valid credentials');
    }
  };

  const handleRegister = (formData: any) => {
    console.log('Registering user:', formData);
    alert('Registration successful! Please login.');
    navigate('/login');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setSidebarOpen(true);
    navigate('/login');
  };

  // Sidebar Component
  const Sidebar = () => {
    const menuItems = [
      { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { path: '/balance-statement', label: 'Balance Statement', icon: FileText },
      { path: '/loan-statement', label: 'Loan Statement', icon: CreditCard }
    ];

    return (
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gradient-to-b from-blue-800 to-blue-900 text-white transition-all duration-300 fixed h-full z-20 shadow-2xl`}>
        <div className="p-4 flex items-center justify-between border-b border-blue-700">
          {sidebarOpen && (
            <div>
              <h2 className="text-xl font-bold">SSID Panel</h2>
              <p className="text-xs text-blue-200 mt-1">Admin Dashboard</p>
            </div>
          )}
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)} 
            className="p-2 hover:bg-blue-700 rounded-lg transition"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        <nav className="mt-6">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = window.location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center ${sidebarOpen ? 'px-6' : 'px-4 justify-center'} py-4 hover:bg-blue-700 transition-all duration-200 ${
                  isActive ? 'bg-blue-700 border-l-4 border-white' : ''
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
            onClick={handleLogout}
            className={`w-full flex items-center ${sidebarOpen ? 'px-6' : 'px-4 justify-center'} py-4 hover:bg-red-600 transition-all duration-200`}
          >
            <LogOut className="w-5 h-5" />
            {sidebarOpen && <span className="ml-3 font-medium">Logout</span>}
          </button>
        </div>
      </div>
    );
  };

  // Header Component
  const Header = () => {
    const initials = userName.split(' ').map(n => n[0]).join('');
    
    return (
      <div className="bg-white shadow-md p-4 flex items-center justify-between sticky top-0 z-10">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Jan Dhan Sanchay Coop. Society</h1>
          <p className="text-xs text-gray-600">Thrift & Credit Society Limited</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right hidden md:block">
            <p className="text-sm font-semibold text-gray-800">{userName}</p>
            <p className="text-xs text-gray-600">Member ID: {memberId}</p>
          </div>
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
            {initials}
          </div>
        </div>
      </div>
    );
  };

  // Main Layout
  const MainLayout = ({ children }: { children: React.ReactNode }) => {
    return (
      <div className="min-h-screen bg-gray-100 flex">
        <Sidebar />
        <div className={`flex-1 ${sidebarOpen ? 'ml-64' : 'ml-20'} transition-all duration-300`}>
          <Header />
          <div className="p-6">
            {children}
          </div>
        </div>
      </div>
    );
  };

  return (
    <Routes>
      {/* Public Routes */}
      <Route 
        path="/login" 
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <LoginPage 
              onLogin={handleLogin} 
              onNavigateToRegister={() => navigate('/register')} 
            />
          )
        } 
      />
      
      <Route 
        path="/register" 
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <RegisterPage 
              onRegister={handleRegister} 
              onNavigateToLogin={() => navigate('/login')} 
            />
          )
        } 
      />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute isAuthenticated={isAuthenticated}>
            <MainLayout>
              <Dashboard />
            </MainLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/balance-statement"
        element={
          <ProtectedRoute isAuthenticated={isAuthenticated}>
            <MainLayout>
              <BalanceStatement />
            </MainLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/loan-statement"
        element={
          <ProtectedRoute isAuthenticated={isAuthenticated}>
            <MainLayout>
              <LoanStatement />
            </MainLayout>
          </ProtectedRoute>
        }
      />

      {/* Default Route */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      
      {/* 404 Route */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

// Wrapper Component
const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
};

export default App;