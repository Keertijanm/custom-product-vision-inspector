import Link from "next/link";
import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">CPV</div>
          <div>
            <div className="brand-name">Custom Product Vision Inspector</div>
            <div className="brand-subtitle">AI product inspection workflow</div>
          </div>
        </div>

        <nav className="nav" aria-label="Main navigation">
          <Link href="/">Dashboard</Link>
          <Link href="/setup">Product Setup</Link>
          <Link href="/inspection">Inspection</Link>
          <Link href="/results">Results</Link>
        </nav>
      </header>

      <main className="content-shell">{children}</main>
    </div>
  );
}
