import { memo } from 'react';

/**
 * AppTemplate — dark-canvas layout for app pages (Dashboard, Vendors, etc.).
 *
 * Props:
 *   navbar   {ReactNode} — NavBar organism (sticky)
 *   children {ReactNode} — main content
 *   footer   {ReactNode} — Footer organism (optional)
 */
function AppTemplate({ navbar, children, footer }) {
  return (
    <div className="min-h-screen flex flex-col bg-ink text-[var(--color-text-inv)]">
      {navbar ? (
        <div className="sticky top-0 z-50">
          {navbar}
        </div>
      ) : null}

      <main className="flex-1">
        {children}
      </main>

      {footer ?? null}
    </div>
  );
}

export default memo(AppTemplate);
