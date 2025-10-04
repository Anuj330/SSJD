import { useState } from 'react';

interface User {
  username: string;
  fullName: string;
  memberId: string;
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = (username: string, password: string) => {
    // This is a mock login - replace with actual API call
    if (username && password) {
      const mockUser: User = {
        username,
        fullName: 'ANUJ MAHTO',
        memberId: '12345'
      };
      setUser(mockUser);
      setIsAuthenticated(true);
      return true;
    }
    return false;
  };

  const register = (formData: any) => {
    // Mock registration - replace with actual API call
    console.log('Registering user:', formData);
    return true;
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  return {
    user,
    isAuthenticated,
    login,
    register,
    logout
  };
};