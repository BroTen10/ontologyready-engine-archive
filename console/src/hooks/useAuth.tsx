import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import api from "../api/client";
import { login as apiLogin, refreshToken as apiRefresh, logout as apiLogout, fetchProfile, type UserProfile } from "../api/endpoints";

interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<string | null>;
}

const AuthContext = createContext<AuthState>({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: async () => {},
  refresh: async () => null,
});

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

function getStoredTokens(): { access: string | null; refresh: string | null } {
  try {
    return {
      access: localStorage.getItem(ACCESS_TOKEN_KEY),
      refresh: localStorage.getItem(REFRESH_TOKEN_KEY),
    };
  } catch {
    return { access: null, refresh: null };
  }
}

function setStoredTokens(access: string | null, refresh: string | null) {
  try {
    if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access);
    else localStorage.removeItem(ACCESS_TOKEN_KEY);
    if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    else localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch { /* ignore quota errors */ }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const setTokens = useCallback((access: string | null, refresh: string | null) => {
    setAccessToken(access);
    setRefreshToken(refresh);
    setStoredTokens(access, refresh);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const tokens = await apiLogin({ username, password });
    setTokens(tokens.access_token, tokens.refresh_token);
  }, [setTokens]);

  const logout = useCallback(async () => {
    try {
      if (refreshToken) {
        await apiLogout();
      }
    } catch { /* server may be down */ }
    setTokens(null, null);
    setStoredTokens(null, null);
    setUser(null);
  }, [setTokens, refreshToken]);

  const refresh = useCallback(async (): Promise<string | null> => {
    if (!refreshToken) return null;
    try {
      const tokens = await apiRefresh(refreshToken);
      setTokens(tokens.access_token, tokens.refresh_token);
      return tokens.access_token;
    } catch {
      setTokens(null, null);
      setUser(null);
      return null;
    }
  }, [refreshToken, setTokens]);

  useEffect(() => {
    const { access, refresh: stored } = getStoredTokens();
    if (access && stored) {
      setAccessToken(access);
      setRefreshToken(stored);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (!accessToken) {
      setUser(null);
      return;
    }
    let cancelled = false;
    api.get<UserProfile>("/auth/profile", {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then((r) => {
        if (!cancelled) setUser(r.data);
      })
      .catch(async () => {
        if (cancelled) return;
        const newToken = await refresh();
        if (newToken) {
          try {
            const r = await api.get<UserProfile>("/auth/profile", {
              headers: { Authorization: `Bearer ${newToken}` },
            });
            if (!cancelled) setUser(r.data);
          } catch {
            if (!cancelled) setUser(null);
          }
        }
      });
    return () => { cancelled = true; };
  }, [accessToken, refresh]);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        refreshToken,
        isAuthenticated: !!user && !!accessToken,
        isLoading,
        login,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
