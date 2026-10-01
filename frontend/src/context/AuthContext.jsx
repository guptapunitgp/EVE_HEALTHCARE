import { useCallback, useEffect, useMemo, useState } from "react";
import api from "../lib/api";
import AuthContext from "./authContext";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(sessionStorage.getItem("eve_token")));

  const refresh = useCallback(async () => {
    if (!sessionStorage.getItem("eve_token")) { setUser(null); setLoading(false); return null; }
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
      return response.data;
    } catch {
      sessionStorage.removeItem("eve_token");
      setUser(null);
      return null;
    } finally { setLoading(false); }
  }, []);

  // eslint-disable-next-line react-hooks/set-state-in-effect -- refresh resolves the saved bearer session asynchronously.
  useEffect(() => { void refresh(); }, [refresh]);

  const acceptSession = useCallback((data) => {
    sessionStorage.setItem("eve_token", data.access_token);
    setUser(data.user);
  }, []);

  const signOut = useCallback(async () => {
    try { await api.post("/auth/logout"); } catch { /* Clear local session even if Redis cannot revoke it. */ }
    sessionStorage.removeItem("eve_token");
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, refresh, acceptSession, signOut }), [user, loading, refresh, acceptSession, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
