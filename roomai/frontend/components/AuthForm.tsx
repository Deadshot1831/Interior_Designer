"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api, ApiError, setToken } from "@/lib/api";

function AuthFormInner({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const isSignup = mode === "signup";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = isSignup
        ? await api.signup(email, password)
        : await api.login(email, password);
      setToken(res.access_token);
      router.push(next);
      router.refresh();
    } catch (err) {
      setError((err as ApiError).message || "Something went wrong.");
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm space-y-6 rounded-2xl border border-black/10 bg-white p-6">
      <div className="space-y-1 text-center">
        <h1 className="text-xl font-semibold">
          {isSignup ? "Create your account" : "Welcome back"}
        </h1>
        <p className="text-sm text-black/50">
          {isSignup
            ? "Get 3 free design credits to start."
            : "Log in to continue designing."}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-black/15 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Password</label>
          <input
            type="password"
            required
            minLength={isSignup ? 8 : undefined}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-black/15 px-3 py-2 text-sm"
          />
          {isSignup && (
            <p className="mt-1 text-xs text-black/40">At least 8 characters.</p>
          )}
        </div>

        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          disabled={busy}
          className="w-full rounded-lg bg-brand py-2.5 font-medium text-white hover:bg-brand-light disabled:opacity-60"
        >
          {busy
            ? "Please wait…"
            : isSignup
              ? "Sign up"
              : "Log in"}
        </button>
      </form>

      <p className="text-center text-sm text-black/50">
        {isSignup ? (
          <>
            Already have an account?{" "}
            <Link href="/login" className="text-brand underline">
              Log in
            </Link>
          </>
        ) : (
          <>
            New here?{" "}
            <Link href="/signup" className="text-brand underline">
              Sign up
            </Link>
          </>
        )}
      </p>
    </div>
  );
}

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  return (
    <Suspense fallback={null}>
      <AuthFormInner mode={mode} />
    </Suspense>
  );
}
