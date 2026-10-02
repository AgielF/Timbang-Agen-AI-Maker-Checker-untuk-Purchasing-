import { BrowserRouter, Routes, Route } from 'react-router-dom';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <div className="min-h-screen flex items-center justify-center">
              <h1 className="text-4xl font-black tracking-tighter text-navy">
                Timbang — scaffold ready
              </h1>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
