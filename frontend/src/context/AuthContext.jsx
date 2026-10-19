import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import * as authApi from "../api/auth";
import { tokenStore } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(tokenStore.get()));

  // On first load, if a token exists, find out who it belongs to.
  useEffect(() => {
    if (!tokenStore.get()) return;
    authApi
      .getMe()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  // The axios interceptor fires this event when the token stops working.
  useEffect(() => {
    const onLogout = () => setUser(null);
    window.addEventListener("chatdoc:logout", onLogout);
    return () => window.removeEventListener("chatdoc:logout", onLogout);
  }, []);

  const handleAuthResult = useCallback((data) => {
    tokenStore.set(data.token);
    setUser(data.user);
  }, []);

  const login = useCallback(
    async (credentials) => handleAuthResult(await authApi.login(credentials)),
    [handleAuthResult]
  );
  const register = useCallback(
    async (details) => handleAuthResult(await authApi.register(details)),
    [handleAuthResult]
  );
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      /* even if the server call fails we still log out locally */
    }
    tokenStore.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
};
