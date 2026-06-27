"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, getToken } from "@/lib/api";
import type { Style } from "@/lib/types";
import { StylePicker } from "@/components/StylePicker";

export default function HomePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [style, setStyle] = useState<Style | null>(null);
  const [dragging, setDragging] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function selectFile(f: File | null) {
    setError(null);
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      setError("Please choose an image file (jpg, png, webp, or heic).");
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  async function handleSubmit() {
    setError(null);
    if (!getToken()) {
      router.push("/login?next=/");
      return;
    }
    if (!file) {
      setError("Upload a photo of your room first.");
      return;
    }
    if (!style) {
      setError("Pick a style.");
      return;
    }
    setSubmitting(true);
    try {
      const room = await api.uploadRoom(file);
      const design = await api.createDesign(room.room_id, style);
      router.push(`/design/${design.id}`);
    } catch (e) {
      const err = e as ApiError;
      if (err.code === "out_of_credits") {
        router.push("/dashboard?upgrade=1");
        return;
      }
      setError(err.message || "Something went wrong. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-10">
      <section className="space-y-3 text-center">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Redesign your room with AI that respects your room
        </h1>
        <p className="mx-auto max-w-2xl text-black/60">
          Upload a photo and get a design report that only describes what&apos;s
          actually in your space — no imaginary windows, no furniture blocking
          your doorway.
        </p>
      </section>

      <section className="mx-auto max-w-2xl space-y-6 rounded-2xl border border-black/10 bg-white p-5 sm:p-7">
        {/* Upload area */}
        <div>
          <label className="mb-2 block text-sm font-medium">
            1. Upload your room
          </label>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              selectFile(e.dataTransfer.files?.[0] ?? null);
            }}
            onClick={() => inputRef.current?.click()}
            className={`flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-4 text-center transition ${
              dragging
                ? "border-brand bg-brand-sand/40"
                : "border-black/15 hover:border-black/30"
            }`}
          >
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={preview}
                alt="Room preview"
                className="max-h-56 rounded-lg object-contain"
              />
            ) : (
              <div className="text-sm text-black/50">
                <p className="font-medium text-black/70">
                  Drag &amp; drop or click to choose a photo
                </p>
                <p className="mt-1">JPG, PNG, WEBP or HEIC · up to 10MB</p>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => selectFile(e.target.files?.[0] ?? null)}
            />
          </div>
        </div>

        {/* Style picker */}
        <div>
          <label className="mb-2 block text-sm font-medium">
            2. Choose a style
          </label>
          <StylePicker value={style} onChange={setStyle} />
        </div>

        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full rounded-lg bg-brand py-3 font-medium text-white transition hover:bg-brand-light disabled:opacity-60"
        >
          {submitting ? "Analyzing your room…" : "Generate design report"}
        </button>
        <p className="text-center text-xs text-black/40">
          Analysis takes ~5–15 seconds. Uses 1 credit.
        </p>
      </section>
    </div>
  );
}
