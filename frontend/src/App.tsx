import { useEffect, useState } from "react";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import { api } from "./services/api";
import type { User } from "./types/api";

const TOKEN_KEY = "leadhive_token";

export default function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setBooting(false);
        return;
      }
      try {
        const currentUser = await api.me(token);
        setUser(currentUser);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      } finally {
        setBooting(false);
      }
    }
    loadUser();
  }, [token]);

  function handleAuth(nextToken: string) {
    localStorage.setItem(TOKEN_KEY, nextToken);
    setToken(nextToken);
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }

  if (booting) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#f7f4ed]">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-ink border-t-leaf" />
      </main>
    );
  }

  if (!token || !user) {
    return <AuthPage onAuth={handleAuth} />;
  }

  return <DashboardPage token={token} user={user} onLogout={handleLogout} />;
}

