"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function Home() {
  const [error, setError] = useState<string | null>(null);

  const connectDrive = async () => {
    setError(null);
    try {
      const res = await api.get("/auth/login");
      window.location.href = res.data.url;
    } catch (e: unknown) {
      const message =
        e && typeof e === "object" && "message" in e
          ? String((e as { message?: string }).message)
          : "Request failed";
      setError(
        `${message}. Is the API running (e.g. uvicorn on port 8000) and reachable?`,
      );
    }
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Document Audit System</h1>
      <button onClick={connectDrive}>
        Connect Google Drive
      </button>
      {error && (
        <p style={{ color: "crimson", marginTop: 16, maxWidth: 480 }}>
          {error}
        </p>
      )}
    </div>
  );
}