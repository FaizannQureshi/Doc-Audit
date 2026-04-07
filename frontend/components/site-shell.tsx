"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function NavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const active = pathname === href;
  return (
    <Link
      href={href}
      className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
      }`}
    >
      {children}
    </Link>
  );
}

export function SiteShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/90">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link href="/" className="flex min-w-0 items-center gap-3">
            <span
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-sm font-bold text-white shadow-sm"
              aria-hidden
            >
              DA
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
                Document Audit
              </span>
              <span className="block text-xs text-slate-500 dark:text-slate-400">
                Compliance workspace
              </span>
            </span>
          </Link>
          <nav className="flex shrink-0 items-center gap-1" aria-label="Main">
            <NavLink href="/">Home</NavLink>
            <NavLink href="/dashboard">Folder audit</NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-slate-200 py-8 dark:border-slate-800">
        <div className="mx-auto max-w-6xl px-4 text-center text-xs text-slate-500 sm:px-6 dark:text-slate-400">
          Scan Drive folders for required documents, expirations, and naming
          issues. Reports can sync to Google Sheets.
        </div>
      </footer>
    </div>
  );
}
