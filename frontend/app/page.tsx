"use client";

import { api } from "@/lib/api";

export default function Home() {
  const connectDrive = async () => {
    const res = await api.get("/auth/login");
    window.location.href = res.data.url;
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Document Audit System</h1>
      <button onClick={connectDrive}>
        Connect Google Drive
      </button>
    </div>
  );
}