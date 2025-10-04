export interface User {
  id: string;
  username: string;
  fullName: string;
  email: string;
  phone: string;
  memberId: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
}

export interface RegisterData {
  fullName: string;
  email: string;
  phone: string;
  username: string;
  password: string;
}