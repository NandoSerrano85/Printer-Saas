import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Designs = lazy(() => import('./pages/Designs'));
const MaskCreator = lazy(() => import('./pages/MaskCreator'));

export default function App() {
  return (
    <TenantProvider>
      <ThemeProvider>
        <Router>
          <AppLayout>
            <Suspense fallback={<LoadingSpinner />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/designs" element={<Designs />} />
                <Route path="/tools/mask-creator" element={<MaskCreator />} />
              </Routes>
            </Suspense>
          </AppLayout>
        </Router>
      </ThemeProvider>
    </TenantProvider>
  );
};