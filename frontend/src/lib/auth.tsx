import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { Navigate, useLocation } from "react-router-dom";
import {
  OpenAPI,
  AuthenticationService,
  type UserRead,
  type UserCreate,
  type UserLogin,
} from "../api";

interface AuthContextType {
  token: string | null;
  user: UserRead | null;
  loading: boolean;
  login: (data: UserLogin) => Promise<void>;
  signup: (data: UserCreate) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
  hasAiAccess: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

function configureApi(token: string | null) {
  OpenAPI.BASE = "/api";
  OpenAPI.TOKEN = token ?? undefined;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("token");
    if (saved) {
      configureApi(saved);
      AuthenticationService.getMeAuthMeGet()
        .then((u) => {
          setToken(saved);
          setUser(u);
        })
        .catch(() => {
          localStorage.removeItem("token");
          configureApi(null);
        })
        .finally(() => setLoading(false));
    } else {
      configureApi(null);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    configureApi(token);
  }, [token]);

  const login = async (data: UserLogin) => {
    const res = await AuthenticationService.loginAuthLoginPost(data);
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const signup = async (data: UserCreate) => {
    const res = await AuthenticationService.signupAuthSignupPost(data);
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const isAdmin = user?.role === "admin";
  const hasAiAccess = isAdmin || !!user?.ai_enabled;

  return (
    <AuthContext.Provider value={{ token, user, loading, login, signup, logout, isAdmin, hasAiAccess }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-surface">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
