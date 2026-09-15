import React, { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => {
    const raw = sessionStorage.getItem("gem-sentinel-session");
    return raw ? JSON.parse(raw) : null;
  });

  const login = (data) => {
    // Store the full response including role
    setSession({
      ...data,
      role: data.role,
      user_id: data.user_id,
    });
    sessionStorage.setItem("gem-sentinel-session", JSON.stringify({
      ...data,
      role: data.role,
      user_id: data.user_id,
    }));
  };

  const logout = () => {
    setSession(null);
    sessionStorage.removeItem("gem-sentinel-session");
  };

  return <AuthContext.Provider value={{ session, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
