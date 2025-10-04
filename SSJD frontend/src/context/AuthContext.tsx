import React, { createContext, useContext, useState, type ReactNode } from 'react';
import type { AuthContextType, RegisterData, User } from '../types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = async (username: string, password: string) => {
    // API call would go here
    const mockUser: User = {
      id: '1',
      username,
      fullName: 'ANUJ MAHTO',
      email: 'anuj@example.com',
      phone: '9999999999',
      memberId: '12345'
    };
    
    setUser(mockUser);
    setIsAuthenticated(true);
  };

  const register = async (userData: RegisterData) => {
    // API call would go here
    console.log('Registering user:', userData);
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};