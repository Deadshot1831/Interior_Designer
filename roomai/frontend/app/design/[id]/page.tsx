"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, getToken, resolveImageUrl } from "@/lib/api";
import type { Design } from "@/lib/types";

export default function DesignPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [design, setDesign] = useState<Design | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push(`/login?next=/design/${params.id}`);
      return;
    }
    let active = true;
    api
      .getDesign(params.id)
      .then((d) => active && setDesign(d))
      .catch((e: ApiError) => active && setError(e.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [params.id, router]);

  if (loading) return <ResultsSkeleton />;

  if (error || !design) {
    return (
      <div className="rounded-xl border border-black/10 bg-white p-8 text-center">
        <p className="text-black/70">{error || "Design not found."}</p>
        <Link href="/" className="mt-4 inline-block text-brand underline">
          Start a new design
        </Link>
      </div>
    );
  }

  if (design.status === "failed") {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-8 text-center">
        <h2 className="text-lg font-semibold">Analysis didn&apos;t complete</h2>
        <p className="mt-2 text-black/70">
          We couldn&apos;t analyze this room. No credit was used — please try
          again.
        </p>
        <Link
          href="/"
          className="mt-4 inline-block rounded-md bg-brand px-4 py-2 text-white"
        >
          Try again
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Original photo */}
      {design.image_url && (
        <section>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={resolveImageUrl(design.image_url)}
            alt="Your room"
            className="max-h-[420px] w-full rounded-2xl object-contain bg-black/5"
          />
        </section>
      )}

      {/* Room type + detected objects */}
      <section className="rounded-2xl border border-black/10 bg-white p-5 sm:p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-2xl font-semibold capitalize">
            {design.room_type || "Room"}
          </h1>
          <span className="text-sm capitalize text-black/50">
            {design.style.replace("_", " ")} style
          </span>
        </div>
        <p className="mt-1 text-sm text-black/50">
          Here&apos;s what we actually detected in your photo:
        </p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {(design.detected_objects || []).map((o, i) => (
            <li
              key={i}
              className="rounded-full border border-black/10 bg-black/[0.03] px-3 py-1 text-sm"
            >
              <span className="font-medium">{o.label}</span>
              {o.location ? (
                <span className="text-black/50"> · {o.location}</span>
              ) : null}
              {o.confidence ? (
                <span className="ml-1 text-xs text-black/40">
                  ({o.confidence})
                </span>
              ) : null}
            </li>
          ))}
          {(!design.detected_objects ||
            design.detected_objects.length === 0) && (
            <li className="text-sm text-black/40">No objects detected.</li>
          )}
        </ul>
      </section>

      {/* Palette */}
      {design.palette && design.palette.length > 0 && (
        <section className="rounded-2xl border border-black/10 bg-white p-5 sm:p-6">
          <h2 className="text-lg font-semibold">Color palette</h2>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {design.palette.map((c, i) => (
              <div key={i} className="space-y-1.5">
                <div
                  className="h-16 w-full rounded-lg border border-black/10"
                  style={{ backgroundColor: c.hex }}
                />
                <p className="text-sm font-medium">{c.name}</p>
                <p className="text-xs uppercase tracking-wide text-black/40">
                  {c.hex}
                </p>
                <p className="text-xs text-black/50">{c.usage}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Furniture suggestions */}
      {design.furniture_suggestions &&
        design.furniture_suggestions.length > 0 && (
          <section className="rounded-2xl border border-black/10 bg-white p-5 sm:p-6">
            <h2 className="text-lg font-semibold">Furniture suggestions</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {design.furniture_suggestions.map((f, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-black/10 p-4"
                >
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-medium capitalize">{f.category}</h3>
                    <span className="rounded-full bg-brand-sand px-2 py-0.5 text-xs font-medium text-brand">
                      ₹{f.est_price_range_inr}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-black/70">{f.description}</p>
                  <p className="mt-2 text-sm text-black/50">
                    <span className="font-medium text-black/60">Placement:</span>{" "}
                    {f.placement_note}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

      {/* Layout notes */}
      {design.layout_notes && (
        <section className="rounded-2xl border border-black/10 bg-white p-5 sm:p-6">
          <h2 className="text-lg font-semibold">Layout advice</h2>
          <p className="mt-2 text-black/70">{design.layout_notes}</p>
        </section>
      )}

      <div className="flex flex-wrap gap-3">
        <Link
          href="/"
          className="rounded-lg bg-brand px-4 py-2 font-medium text-white hover:bg-brand-light"
        >
          Design another room
        </Link>
        <Link
          href="/dashboard"
          className="rounded-lg border border-black/15 px-4 py-2 font-medium hover:border-black/30"
        >
          View past designs
        </Link>
      </div>
    </div>
  );
}

function ResultsSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="h-72 w-full rounded-2xl bg-black/5" />
      <div className="h-32 w-full rounded-2xl bg-black/5" />
      <div className="h-40 w-full rounded-2xl bg-black/5" />
    </div>
  );
}
