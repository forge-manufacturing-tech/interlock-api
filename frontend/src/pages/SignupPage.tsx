import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../lib/auth";
import { AuthenticationService } from "../api";
import Navbar from "../components/Navbar";

export default function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { data: settings, isLoading: settingsLoading } = useQuery({
    queryKey: ["system-settings"],
    queryFn: () => AuthenticationService.getSystemSettingsAuthSettingsGet(),
  });

  const signupDisabled = settings && !settings.signup_enabled;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (signupDisabled) {
      setError("Signups are currently disabled by an administrator.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await signup({ email, password, name: name || undefined });
      navigate("/dashboard");
    } catch {
      setError("Signup failed. Try a different email.");
    } finally {
      setLoading(false);
    }
  };

  if (settingsLoading) {
    return (
      <div className="min-h-screen bg-surface">
        <Navbar />
        <div className="flex min-h-screen items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </div>
    );
  }

  if (signupDisabled) {
    return (
      <div className="min-h-screen bg-surface">
        <Navbar />
        <div className="flex min-h-screen items-center justify-center px-4 pt-14">
          <div className="w-full max-w-md">
            <div className="rounded-md border border-border bg-surface-light p-8 space-y-6 text-center">
              <h2 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
                Signups Disabled
              </h2>
              <p className="text-text-secondary">
                New account registration is currently disabled. Contact an administrator for access.
              </p>
              <p className="text-sm text-text-muted">
                Already have an account?{" "}
                <Link to="/login" className="text-primary hover:underline">
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <div className="flex min-h-screen items-center justify-center px-4 pt-14">
        <div className="w-full max-w-md">
          <form
            onSubmit={handleSubmit}
            className="rounded-md border border-border bg-surface-light p-8 space-y-6"
          >
            <h2 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary text-center">
              Create your account
            </h2>

            {error && (
              <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-text-secondary">
                  Name <span className="text-text-muted">(optional)</span>
                </label>
                <input
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface px-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-text-secondary">
                  Email
                </label>
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full rounded-md border border-border bg-surface px-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-text-secondary">
                  Password
                </label>
                <input
                  type="password"
                  placeholder="Min 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full rounded-md border border-border bg-surface px-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-text-secondary">
                  Confirm Password
                </label>
                <input
                  type="password"
                  placeholder="Repeat your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full rounded-md border border-border bg-surface px-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-primary px-4 py-2.5 font-mono text-sm font-medium uppercase tracking-wider text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? "Creating account..." : "CREATE ACCOUNT"}
            </button>

            <p className="text-center text-sm text-text-muted">
              Already have an account?{" "}
              <Link to="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
