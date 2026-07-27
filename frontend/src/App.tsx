import { BrowserRouter, Navigate, Route, Routes, useParams } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { RequireAuth } from "./components/RequireAuth";
import { AuthProvider } from "./lib/auth";
import { AuthCallbackPage } from "./pages/AuthCallbackPage";
import { CallSiteExplorerPage } from "./pages/CallSiteExplorerPage";
import { ChangeDetailPage } from "./pages/ChangeDetailPage";
import { ChangeFeedPage } from "./pages/ChangeFeedPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { SettingsPage } from "./pages/SettingsPage";
import { WatchedApisPage } from "./pages/WatchedApisPage";

function RedirectChangeDetail() {
  const { id } = useParams();
  return <Navigate to={`/app/changes/${id}`} replace />;
}

function RedirectChangeExplorer() {
  const { id } = useParams();
  return <Navigate to={`/app/changes/${id}/explorer`} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />

          <Route element={<RequireAuth />}>
            <Route path="/app" element={<AppShell />}>
              <Route index element={<DashboardPage />} />
              <Route path="apis" element={<WatchedApisPage />} />
              <Route path="changes" element={<ChangeFeedPage />} />
              <Route path="changes/:id" element={<ChangeDetailPage />} />
              <Route path="changes/:id/explorer" element={<CallSiteExplorerPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Route>

          {/* Legacy paths */}
          <Route path="/changes" element={<Navigate to="/app/changes" replace />} />
          <Route path="/changes/:id" element={<RedirectChangeDetail />} />
          <Route path="/changes/:id/explorer" element={<RedirectChangeExplorer />} />
          <Route path="/settings" element={<Navigate to="/app/settings" replace />} />
          <Route path="/apis" element={<Navigate to="/app/apis" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
