import React, { type ReactNode } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

interface MainLayoutProps {
  children: ReactNode;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  currentPage: string;
  setCurrentPage: (page: string) => void;
  userName: string;
  memberId: string;
  onLogout: () => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  sidebarOpen,
  setSidebarOpen,
  currentPage,
  setCurrentPage,
  userName,
  memberId,
  onLogout
}) => {
  return (
    <div className="min-h-screen bg-gray-100 flex">
      <Sidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        onLogout={onLogout}
      />

      <div className={`flex-1 ${sidebarOpen ? 'ml-64' : 'ml-20'} transition-all duration-300`}>
        <Header userName={userName} memberId={memberId} />
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

export default MainLayout;