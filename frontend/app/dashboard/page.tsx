"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import {
  Alert,
  Button,
  Card,
  CardHeader,
  Input,
  Label,
  Spinner,
  StatusPill,
} from "@/components/ui";

type AuditPayload = {
  audit: {
    client_name: string;
    folder_id: string;
    folder_url: string;
    status: string;
    missing_documents: string[];
    expired_documents: Record<string, unknown>[];
    expiring_soon: Record<string, unknown>[];
    mislabeled_or_suspicious: Record<string, unknown>[];
    classified_files: Record<string, unknown>[];
    scanned_at: string;
  };
  sheet_url: string | null;
  sheet_error: string | null;
  new_spreadsheet_id: string | null;
};

function Section({
  title,
  icon,
  children,
  empty,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  empty?: boolean;
}) {
  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
      <div className="mb-4 flex items-center gap-2">
        <span className="text-slate-500 dark:text-slate-400">{icon}</span>
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
          {title}
        </h3>
      </div>
      {empty ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">None</p>
      ) : (
        children
      )}
    </section>
  );
}

export default function Dashboard() {
  const [folderId, setFolderId] = useState("");
  const [clientName, setClientName] = useState("");
  const [spreadsheetId, setSpreadsheetId] = useState("");
  const [createSheet, setCreateSheet] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AuditPayload | null>(null);

  const runFolderAudit = async () => {
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post<AuditPayload>("/audit/folder", {
        folder_id: folderId.trim(),
        client_name: clientName.trim(),
        spreadsheet_id: spreadsheetId.trim() || undefined,
        create_sheet_if_missing: createSheet,
      });
      setResult(res.data);
    } catch (e: unknown) {
      let msg = "Request failed";
      if (e && typeof e === "object" && "response" in e) {
        const ax = e as {
          response?: { data?: { detail?: string }; status?: number };
        };
        const detail = ax.response?.data?.detail;
        if (typeof detail === "string") msg = detail;
      } else if (e && typeof e === "object" && "message" in e) {
        msg = String((e as { message?: string }).message);
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const a = result?.audit;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Folder audit
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-400">
            Enter a Drive folder ID to scan all files inside it (including
            subfolders). Connect Google from the{" "}
            <Link
              href="/"
              className="font-medium text-indigo-600 underline-offset-4 hover:underline dark:text-indigo-400"
            >
              home page
            </Link>{" "}
            first if you have not signed in.
          </p>
        </div>
        <Link
          href="/"
          className="shrink-0 text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
        >
          ← Back to home
        </Link>
      </div>

      <Card>
        <CardHeader
          title="Run scan"
          description="Paste the folder ID from the Google Drive URL (the segment after /folders/)."
        />
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Label htmlFor="folder-id">Folder ID</Label>
            <Input
              id="folder-id"
              value={folderId}
              onChange={(e) => setFolderId(e.target.value)}
              placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
              autoComplete="off"
            />
          </div>
          <div>
            <Label htmlFor="client">Client / caregiver name</Label>
            <Input
              id="client"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              placeholder="Shown in your Sheet row"
              autoComplete="off"
            />
          </div>
          <div>
            <Label htmlFor="sheet">Google Sheet ID (optional)</Label>
            <Input
              id="sheet"
              value={spreadsheetId}
              onChange={(e) => setSpreadsheetId(e.target.value)}
              placeholder="Or set AUDIT_SPREADSHEET_ID on the server"
              autoComplete="off"
            />
          </div>
          <div className="flex items-center sm:col-span-2">
            <label className="flex cursor-pointer items-center gap-3 text-sm text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={createSheet}
                onChange={(e) => setCreateSheet(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-600"
              />
              Create a new Google Sheet for this run if no Sheet is configured
            </label>
          </div>
        </div>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Button
            onClick={runFolderAudit}
            disabled={loading || !folderId.trim()}
            className="min-w-[160px]"
          >
            {loading ? (
              <>
                <Spinner className="text-white" />
                Scanning…
              </>
            ) : (
              "Run audit"
            )}
          </Button>
          {!folderId.trim() ? (
            <span className="text-xs text-slate-500">Enter a folder ID to enable.</span>
          ) : null}
        </div>
      </Card>

      <div className="mt-8 space-y-4">
        {error ? <Alert variant="error">{error}</Alert> : null}
        {result?.sheet_error ? (
          <Alert variant="error">
            <span className="font-medium">Sheet export failed.</span>{" "}
            {result.sheet_error}
          </Alert>
        ) : null}
        {result?.sheet_url ? (
          <Alert variant="success">
            <span className="font-medium">Report logged to Sheets.</span>{" "}
            <a
              href={result.sheet_url}
              target="_blank"
              rel="noreferrer"
              className="font-medium underline underline-offset-2"
            >
              Open spreadsheet
            </a>
          </Alert>
        ) : null}
        {result?.new_spreadsheet_id ? (
          <Alert variant="info">
            New spreadsheet created. Save{" "}
            <code className="rounded bg-indigo-100/80 px-1.5 py-0.5 font-mono text-xs dark:bg-indigo-950/80">
              AUDIT_SPREADSHEET_ID={result.new_spreadsheet_id}
            </code>{" "}
            on the server for future runs.
          </Alert>
        ) : null}
      </div>

      {a ? (
        <div className="mt-10 space-y-6">
          <div className="flex flex-col gap-4 rounded-2xl border border-slate-200/80 bg-gradient-to-br from-slate-50 to-white p-6 dark:border-slate-800 dark:from-slate-900/80 dark:to-slate-950 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Summary
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <StatusPill status={a.status} />
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  {a.client_name}
                </span>
              </div>
              {a.folder_url ? (
                <a
                  href={a.folder_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                >
                  Open folder in Drive →
                </a>
              ) : null}
            </div>
            <div className="text-right text-xs text-slate-500 dark:text-slate-400">
              <div>Scanned (UTC)</div>
              <div className="mt-1 font-mono text-sm text-slate-700 dark:text-slate-300">
                {new Date(a.scanned_at).toLocaleString()}
              </div>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Section
              title="Missing documents"
              empty={a.missing_documents.length === 0}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
            >
              <ul className="space-y-2">
                {a.missing_documents.map((m) => (
                  <li
                    key={m}
                    className="flex items-center gap-2 text-sm text-slate-800 dark:text-slate-200"
                  >
                    <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    {m}
                  </li>
                ))}
              </ul>
            </Section>

            <Section
              title="Expired"
              empty={a.expired_documents.length === 0}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              }
            >
              <ul className="space-y-3">
                {a.expired_documents.map((row, i) => (
                  <li key={i} className="text-sm leading-snug text-slate-800 dark:text-slate-200">
                    <span className="font-medium">
                      {(row.document as string) || "Document"}
                    </span>
                    <span className="text-slate-500 dark:text-slate-400">
                      {" "}
                      — {(row.file as string) || ""}
                    </span>
                    {(row.expiry_date as string) ? (
                      <span className="mt-0.5 block text-xs text-red-600 dark:text-red-400">
                        Expired {(row.expiry_date as string)}
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </Section>

            <Section
              title="Expiring soon"
              empty={a.expiring_soon.length === 0}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            >
              <ul className="space-y-3">
                {a.expiring_soon.map((row, i) => (
                  <li key={i} className="text-sm text-slate-800 dark:text-slate-200">
                    <span className="font-medium">
                      {(row.document as string) || "Document"}
                    </span>
                    {" — "}
                    {(row.file as string) || ""}
                    <span className="ml-2 rounded-md bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900 dark:bg-amber-950/80 dark:text-amber-200">
                      {(row.days_remaining as number) ?? "?"} days left
                    </span>
                  </li>
                ))}
              </ul>
            </Section>

            <Section
              title="Flags & naming"
              empty={a.mislabeled_or_suspicious.length === 0}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
              }
            >
              <ul className="space-y-4">
                {a.mislabeled_or_suspicious.map((row, i) => (
                  <li key={i} className="text-sm">
                    <div className="font-medium text-slate-900 dark:text-white">
                      {(row.file as string) || "File"}
                    </div>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">
                      {(row.reason as string) || ""}
                    </p>
                  </li>
                ))}
              </ul>
            </Section>
          </div>

          <details className="group rounded-2xl border border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-900/40">
            <summary className="cursor-pointer list-none px-5 py-4 text-sm font-semibold text-slate-900 marker:hidden dark:text-white [&::-webkit-details-marker]:hidden">
              <span className="flex items-center justify-between gap-2">
                Classified files ({a.classified_files.length})
                <span className="text-slate-400 transition group-open:rotate-180">▼</span>
              </span>
            </summary>
            <div className="border-t border-slate-100 px-5 pb-5 pt-2 dark:border-slate-800">
              <pre className="max-h-80 overflow-auto rounded-xl bg-slate-950/5 p-4 text-xs leading-relaxed text-slate-800 dark:bg-black/30 dark:text-slate-300">
                {JSON.stringify(a.classified_files, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      ) : null}
    </div>
  );
}
