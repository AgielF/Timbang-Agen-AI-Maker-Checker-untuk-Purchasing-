import { memo } from 'react';

/**
 * WorkbenchTemplate — dark-canvas layout for workbench pages
 * (Maker, Checker, Validate, Risk Report).
 *
 * Props:
 *   navbar     {ReactNode} — NavBar organism (sticky)
 *   header     {ReactNode} — PageHeader organism
 *   inputZone  {ReactNode} — SearchBar / form area
 *   resultZone {ReactNode} — Panel / Table / Grid
 *   footer     {ReactNode} — Footer organism (optional)
 */
function WorkbenchTemplate({ navbar, header, inputZone, resultZone, footer }) {
  return (
    <div className="min-h-screen flex flex-col bg-ink text-[var(--color-text-inv)]">
      {navbar ? (
        <div className="sticky top-0 z-50">
          {navbar}
        </div>
      ) : null}

      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-6 py-12 flex flex-col gap-8">
          {header}
          {inputZone}
          {resultZone}
        </div>
      </main>

      {footer ?? null}
    </div>
  );
}

export default memo(WorkbenchTemplate);
