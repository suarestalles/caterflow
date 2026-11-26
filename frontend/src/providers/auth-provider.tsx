
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export type AuthSession = {
  user: {
    id: string;
    full_name: string;
    email: string;
  };
  tenant?: {
    id: string;
    name: string;
  };
  is_platform_admin?: boolean;
};

type AuthContextValue = {
  session: AuthSession | null;
  isLoading: boolean;
  error: string | null;
  reloadSession: () => Promise<boolean>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

// Compartilha a mesma requisição durante montagens simultâneas,
// inclusive as verificações adicionais do React Strict Mode.
let sessionRequest: Promise<AuthSession | null> | null = null;

async function requestSession(): Promise<AuthSession | null> {
  if (!sessionRequest) {
    sessionRequest = fetch("/api/auth/session", {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
    })
      .then(async (response) => {
        if (!response.ok) return null;
        return (await response.json()) as AuthSession;
      })
      .finally(() => {
        sessionRequest = null;
      });
  }

  return sessionRequest;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reloadSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const currentSession = await requestSession();
      setSession(currentSession);
      return currentSession !== null;
    } catch {
      setSession(null);
      setError("Não foi possível verificar sua sessão. Verifique sua conexão.");
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "same-origin",
      });
    } finally {
      setSession(null);
    }
  }, []);

  useEffect(() => {
    void reloadSession();
  }, [reloadSession]);

  return (
    <AuthContext.Provider
      value={{
        session,
        isLoading,
        error,
        reloadSession,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider.");
  }

  return context;
}
