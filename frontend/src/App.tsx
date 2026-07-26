import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { CallSiteExplorerPage } from "./pages/CallSiteExplorerPage";
import { ChangeDetailPage } from "./pages/ChangeDetailPage";
import { ChangeFeedPage } from "./pages/ChangeFeedPage";
import { SettingsPage } from "./pages/SettingsPage";
import { WatchedApisPage } from "./pages/WatchedApisPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<WatchedApisPage />} />
          <Route path="changes" element={<ChangeFeedPage />} />
          <Route path="changes/:id" element={<ChangeDetailPage />} />
          <Route path="changes/:id/explorer" element={<CallSiteExplorerPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
