"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api, ApiError, getToken, resolveImageUrl } from "@/lib/api";
import type { Design } from "@/lib/types";
import { useAuth } from "@/lib/useAuth";

function DashboardInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const [designs, setDesigns] = useState<Design[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const showUpgrade =
    searchParams.get("upgrade") === "1" ||
    (user !== null && user.credits_remaining === 0);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login?next=/dashboard");
      return;
    }
    api
      .myDesigns()
      .then(setDesigns)
      .catch((e: ApiError) => setError(e.message));
  }, [router]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Your designs</h1>
        <Link
          href="/"
          className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-light"
        >
          New design
        </Link>
      </div>

      {showUpgrade && <UpgradePrompt />}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {designs === null ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl bg-black/5" />
          ))}
        </div>
      ) : designs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-black/15 p-10 text-center text-black/50">
          <p>No designs yet.</p>
          <Link href="/" className="mt-2 inline-block text-brand underline">
            Create your first one
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {designs.map((d) => (
            <Link
              key={d.id}
              href={`/design/${d.id}`}
              className="group overflow-hidden rounded-xl border border-black/10 bg-white transition hover:shadow-md"
            >
              <div className="aspect-[4/3] w-full bg-black/5">
                {d.image_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={resolveImageUrl(d.image_url)}
                    alt={d.room_type || "Room"}
                    className="h-full w-full object-cover"
                  />
                )}
              </div>
              <div className="flex items-center justify-between p-3">
                <div>
                  <p className="font-medium capitalize">
                    {d.room_type || "Room"}
                  </p>
                  <p className="text-xs capitalize text-black/50">
                    {d.style.replace("_", " ")}
                  </p>
                </div>
                {d.status === "failed" && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700">
                    failed
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function UpgradePrompt() {
  // TODO(phase2): replace this email-capture stub with real Stripe checkout.
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  return (
    <div className="rounded-xl border border-brand/30 bg-brand-sand/40 p-5">
      <h2 className="font-semibold text-brand">You&apos;re out of credits</h2>
      <p className="mt-1 text-sm text-black/70">
        Paid plans are coming soon. Leave your email and we&apos;ll notify you
        when upgrades are available.
      </p>
      {done ? (
        <p className="mt-3 text-sm font-medium text-brand">
          Thanks — we&apos;ll be in touch!
        </p>
      ) : (
        <form
          className="mt-3 flex flex-col gap-2 sm:flex-row"
          onSubmit={(e) => {
            e.preventDefault();
            if (email) setDone(true);
          }}
        >
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="flex-1 rounded-md border border-black/15 px-3 py-2 text-sm"
          />
          <button className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white">
            Notify me
          </button>
        </form>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={null}>
      <DashboardInner />
    </Suspense>
  );
}
