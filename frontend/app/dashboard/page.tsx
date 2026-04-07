"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function Dashboard() {
  const [result, setResult] = useState<any>(null);

  const runAudit = async () => {
    const files = [
      { name: "Faizan_passport.pdf" },
      { name: "police_clearance.pdf" },
    ];

    const res = await api.post("/audit/run", files);
    setResult(res.data);
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Dashboard</h1>

      <button onClick={runAudit}>
        Run Audit
      </button>

      {result && (
        <pre>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}