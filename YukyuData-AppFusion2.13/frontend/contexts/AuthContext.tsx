import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient, UserInfo } from '../services/apiClient';

interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (apiClient.isAuthenticated()) {
        // Verify token is still valid
        try {
          const response = await apiClient.fetch('/auth/verify');
          if (response.ok) {
            setUser(apiClient.getUser());
          } else {
            // Try refresh
            const refreshed = await apiClient.refreshAccessToken();
            if (refreshed) {
              setUser(apiClient.getUser());
            } else {
              apiClient.clearTokens();
            }
          }
        } catch {
          apiClient.clearTokens();
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const tokens = await apiClient.login(username, password);
    setUser({ username: tokens.username, role: tokens.role });
  }, []);

  const logout = useCallback(async () => {
    await apiClient.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
