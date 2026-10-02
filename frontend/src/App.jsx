import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Spinner from './components/atoms/Spinner';

// Landing is NOT lazy — must render instantly as the entry point
import LandingPage from './pages/LandingPage';

const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

// ─── Placeholders for Iterasi 3B ────────────────────────────────────────────
function Placeholder({ title }) {
  return (
    <div className="min-h-screen bg-ink text-[var(--color-text-inv)] flex items-center justify-center">
      <p className="font-mono text-sm text-[var(--color-text-inv-mute)]">
        {title} — coming in Iteration 3B
      </p>
    </div>
  );
}

// ─── Suspense fallback ───────────────────────────────────────────────────────
function LoadingScreen() {
  return (
    <div className="min-h-screen bg-ink flex items-center justify-center">
      <Spinner size="lg" />
    </div>
  );
}

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          <Route path="/"                    element={<LandingPage />} />
          <Route path="/dashboard"           element={<Placeholder title="Dashboard" />} />
          <Route path="/maker"               element={<Placeholder title="Maker" />} />
          <Route path="/maker/validate"      element={<Placeholder title="Maker / Validate" />} />
          <Route path="/checker"             element={<Placeholder title="Checker" />} />
          <Route path="/checker/risk-report" element={<Placeholder title="Checker / Risk Report" />} />
          <Route path="/vendors"             element={<Placeholder title="Vendors" />} />
          <Route path="/findings"            element={<Placeholder title="Findings" />} />
          <Route path="/about"               element={<Placeholder title="About" />} />
          <Route path="*"                    element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
