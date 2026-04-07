"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { Alert, Button } from "@/components/ui";

export default function Home() {
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);

  const connectDrive = async () => {
    setError(null);
    setConnecting(true);
    try {
      const res = await api.get<{ url: string }>("/auth/login");
      window.location.href = res.data.url;
    } catch (e: unknown) {
      const message =
        e && typeof e === "object" && "message" in e
          ? String((e as { message?: string }).message)
          : "Request failed";
      setError(
        `${message}. Ensure the API is running (e.g. uvicorn on port 8000) and reachable from this app.`,
      );
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <div className="mx-auto max-w-3xl text-center">
        <p className="text-sm font-medium uppercase tracking-wide text-indigo-600 dark:text-indigo-400">
          Compliance-ready document checks
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl dark:text-white">
          Audit Drive folders with confidence
        </h1>
        <p className="mt-6 text-lg leading-relaxed text-slate-600 dark:text-slate-400">
          Connect Google Drive, scan client folders recursively, and surface
          missing files, expired documents, and naming or structure issues—then
          log results to Sheets for your team.
        </p>
        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
          <Button
            onClick={connectDrive}
            disabled={connecting}
            className="min-w-[200px] px-8 py-3"
          >
            {connecting ? "Opening Google…" : "Connect Google Drive"}
          </Button>
          <Link
            href="/dashboard"
            className="inline-flex min-w-[200px] items-center justify-center rounded-xl border border-slate-200 bg-white px-8 py-3 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800 dark:focus-visible:ring-offset-slate-950"
          >
            Go to folder audit
          </Link>
        </div>
        {error ? (
          <div className="mx-auto mt-8 max-w-lg text-left">
            <Alert variant="error">{error}</Alert>
          </div>
        ) : null}
      </div>

      <div className="mx-auto mt-20 grid max-w-5xl gap-6 sm:grid-cols-3">
        {[
          {
            title: "Deep folder scans",
            body: "Walks subfolders and classifies files against your required document types.",
          },
          {
            title: "Expiry awareness",
            body: "Parses dates from filenames and highlights expired or soon-to-expire items.",
          },
          {
            title: "Sheet-ready reports",
            body: "Append each run to Google Sheets for a shareable audit trail.",
          },
        ].map((item) => (
          <div
            key={item.title}
            className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/40"
          >
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              {item.title}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
              {item.body}
            </p>
          </div>
        ))}
      </div>

      <p className="mx-auto mt-14 max-w-2xl text-center text-xs text-slate-500 dark:text-slate-500">
        After changing API scopes, disconnect and connect again in Google so
        new permissions apply.
      </p>
    </div>
  );
}
