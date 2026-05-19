import { FormEvent, useState } from "react";
import { ArrowRight, LockKeyhole, Mail } from "lucide-react";
import { api } from "../services/api";

type Props = {
  onAuth: (token: string) => void;
};

export default function AuthPage({ onAuth }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response =
        mode === "login" ? await api.login(email, password) : await api.register(email, password);
      onAuth(response.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f4ed] text-ink">
      <section className="mx-auto grid min-h-screen max-w-6xl items-center gap-10 px-6 py-10 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <p className="mb-4 text-sm font-semibold uppercase tracking-wide text-leaf">LeadHive Automation</p>
          <h1 className="max-w-2xl text-4xl font-semibold leading-tight md:text-6xl">
            Find weak websites and turn the review into ethical outreach.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-slate-700">
            Collect public business records, score websites, draft personalized emails, and keep every outreach status visible.
          </p>
        </div>

        <form onSubmit={submit} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-6 flex rounded-md bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`focus-ring flex-1 rounded px-4 py-2 text-sm font-semibold ${
                mode === "login" ? "bg-white shadow-sm" : "text-slate-600"
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`focus-ring flex-1 rounded px-4 py-2 text-sm font-semibold ${
                mode === "register" ? "bg-white shadow-sm" : "text-slate-600"
              }`}
            >
              Create account
            </button>
          </div>

          <label className="mb-2 block text-sm font-medium text-slate-700">Email</label>
          <div className="mb-4 flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2">
            <Mail className="h-4 w-4 text-slate-500" />
            <input
              className="w-full bg-transparent outline-none"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              autoComplete="email"
              required
            />
          </div>

          <label className="mb-2 block text-sm font-medium text-slate-700">Password</label>
          <div className="mb-4 flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2">
            <LockKeyhole className="h-4 w-4 text-slate-500" />
            <input
              className="w-full bg-transparent outline-none"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
            />
          </div>

          {error ? <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

          <button
            className="focus-ring flex w-full items-center justify-center gap-2 rounded-md bg-ink px-4 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
            disabled={loading}
          >
            {loading ? "Working..." : mode === "login" ? "Sign in" : "Create account"}
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>
      </section>
    </main>
  );
}
