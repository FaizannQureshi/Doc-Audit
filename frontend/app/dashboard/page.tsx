"use client";

import { useState } from "react";
import { api } from "@/lib/api";

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
      const msg =
        e && typeof e === "object" && "message" in e
          ? String((e as { message?: string }).message)
          : "Request failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const a = result?.audit;

  return (
    <div style={{ padding: 40, maxWidth: 920, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontWeight: 600, marginBottom: 8 }}>Folder audit</h1>
      <p style={{ color: "#444", marginBottom: 24, lineHeight: 1.5 }}>
        Scans a Google Drive folder recursively, checks required documents, parses
        dates from filenames for expiry, and flags structure or naming issues. Connect
        Drive from the home page first; after updating scopes you may need to sign in
        again.
      </p>

      <div
        style={{
          display: "grid",
          gap: 12,
          marginBottom: 20,
          padding: 20,
          background: "#f6f7f9",
          borderRadius: 8,
        }}
      >
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>Folder ID</span>
          <input
            value={folderId}
            onChange={(e) => setFolderId(e.target.value)}
            placeholder="from the Drive URL: …/folders/THIS_PART"
            style={{ padding: 10, borderRadius: 6, border: "1px solid #ccc" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>Client / caregiver name</span>
          <input
            value={clientName}
            onChange={(e) => setClientName(e.target.value)}
            placeholder="Shown in the Sheet row"
            style={{ padding: 10, borderRadius: 6, border: "1px solid #ccc" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>
            Google Sheet ID (optional)
          </span>
          <input
            value={spreadsheetId}
            onChange={(e) => setSpreadsheetId(e.target.value)}
            placeholder="…/spreadsheets/d/SHEET_ID or set AUDIT_SPREADSHEET_ID on the API"
            style={{ padding: 10, borderRadius: 6, border: "1px solid #ccc" }}
          />
        </label>
        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: 14,
            cursor: "pointer",
          }}
        >
          <input
            type="checkbox"
            checked={createSheet}
            onChange={(e) => setCreateSheet(e.target.checked)}
          />
          Create a new audit Sheet if none configured
        </label>
        <button
          type="button"
          onClick={runFolderAudit}
          disabled={loading || !folderId.trim()}
          style={{
            padding: "12px 18px",
            borderRadius: 6,
            border: "none",
            background: loading || !folderId.trim() ? "#aaa" : "#1a73e8",
            color: "#fff",
            fontWeight: 600,
            cursor: loading || !folderId.trim() ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Scanning…" : "Run audit"}
        </button>
      </div>

      {error && (
        <p style={{ color: "#b00020", marginBottom: 16 }}>{error}</p>
      )}

      {result?.sheet_error && (
        <p style={{ color: "#b00020", marginBottom: 16 }}>
          Sheet export failed: {result.sheet_error}
        </p>
      )}

      {result?.sheet_url && (
        <p style={{ marginBottom: 16 }}>
          <a href={result.sheet_url} target="_blank" rel="noreferrer">
            Open audit log (Google Sheet)
          </a>
        </p>
      )}

      {result?.new_spreadsheet_id && (
        <p style={{ marginBottom: 16, fontSize: 14, color: "#333" }}>
          New spreadsheet ID (save as{" "}
          <code style={{ background: "#eee", padding: "2px 6px" }}>
            AUDIT_SPREADSHEET_ID
          </code>{" "}
          for repeat runs):{" "}
          <strong>{result.new_spreadsheet_id}</strong>
        </p>
      )}

      {a && (
        <div style={{ display: "grid", gap: 20 }}>
          <section>
            <h2 style={{ fontSize: 18, marginBottom: 8 }}>Summary</h2>
            <p>
              <strong>Status:</strong> {a.status} · <strong>Client:</strong>{" "}
              {a.client_name}
            </p>
            {a.folder_url ? (
              <p>
                <strong>Folder:</strong>{" "}
                <a href={a.folder_url} target="_blank" rel="noreferrer">
                  {a.folder_url}
                </a>
              </p>
            ) : null}
            <p style={{ fontSize: 13, color: "#666" }}>
              Scanned: {a.scanned_at}
            </p>
          </section>

          <section>
            <h2 style={{ fontSize: 18, marginBottom: 8 }}>Missing</h2>
            {a.missing_documents.length === 0 ? (
              <p>None</p>
            ) : (
              <ul>
                {a.missing_documents.map((m) => (
                  <li key={m}>{m}</li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2 style={{ fontSize: 18, marginBottom: 8 }}>Expired</h2>
            {a.expired_documents.length === 0 ? (
              <p>None</p>
            ) : (
              <ul style={{ paddingLeft: 20 }}>
                {a.expired_documents.map((row, i) => (
                  <li key={i} style={{ marginBottom: 6 }}>
                    {(row.document as string) || "Document"} —{" "}
                    {(row.file as string) || ""} (exp{" "}
                    {(row.expiry_date as string) || ""})
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2 style={{ fontSize: 18, marginBottom: 8 }}>
              Expiring soon (warning)
            </h2>
            {a.expiring_soon.length === 0 ? (
              <p>None</p>
            ) : (
              <ul style={{ paddingLeft: 20 }}>
                {a.expiring_soon.map((row, i) => (
                  <li key={i} style={{ marginBottom: 6 }}>
                    {(row.document as string) || "Document"} —{" "}
                    {(row.file as string) || ""} (
                    {(row.days_remaining as number) ?? "?"} days)
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2 style={{ fontSize: 18, marginBottom: 8 }}>Flags / mislabeled</h2>
            {a.mislabeled_or_suspicious.length === 0 ? (
              <p>None</p>
            ) : (
              <ul style={{ paddingLeft: 20 }}>
                {a.mislabeled_or_suspicious.map((row, i) => (
                  <li key={i} style={{ marginBottom: 8 }}>
                    <strong>{(row.file as string) || "File"}</strong>
                    <br />
                    <span style={{ color: "#555" }}>
                      {(row.reason as string) || ""}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <details>
            <summary style={{ cursor: "pointer", fontWeight: 600 }}>
              Classified files ({a.classified_files.length})
            </summary>
            <pre
              style={{
                marginTop: 12,
                padding: 12,
                background: "#f6f7f9",
                borderRadius: 6,
                overflow: "auto",
                fontSize: 12,
              }}
            >
              {JSON.stringify(a.classified_files, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
