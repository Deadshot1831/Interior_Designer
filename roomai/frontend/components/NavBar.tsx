"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/useAuth";

export function NavBar() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-10 border-b border-black/10 bg-[var(--background)]/80 backdrop-blur">
      <nav className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Room<span className="text-brand">AI</span>
        </Link>
        <div className="flex items-center gap-3 text-sm">
          {loading ? null : user ? (
            <>
              <Link href="/dashboard" className="hover:text-brand">
                Dashboard
              </Link>
              <span className="rounded-full bg-brand-sand px-3 py-1 text-xs font-medium text-brand">
                {user.credits_remaining} credit
                {user.credits_remaining === 1 ? "" : "s"}
              </span>
              <button
                onClick={handleLogout}
                className="text-black/60 hover:text-black"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="hover:text-brand">
                Log in
              </Link>
              <Link
                href="/signup"
                className="rounded-md bg-brand px-3 py-1.5 font-medium text-white hover:bg-brand-light"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
