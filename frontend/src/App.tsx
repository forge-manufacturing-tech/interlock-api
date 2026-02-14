import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { RequireAuth } from "./lib/auth";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const DashboardLayout = lazy(() => import("./components/DashboardLayout"));
const PartsPage = lazy(() => import("./pages/PartsPage"));
const TreesPage = lazy(() => import("./pages/TreesPage"));
const IngestPage = lazy(() => import("./pages/IngestPage"));
const AgentPage = lazy(() => import("./pages/AgentPage"));
const ApiKeysPage = lazy(() => import("./pages/ApiKeysPage"));

const Loading = () => (
  <div className="flex h-screen w-screen items-center justify-center bg-surface">
    <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
  </div>
);

export default function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <DashboardLayout />
            </RequireAuth>
          }
        >
          <Route index element={<PartsPage />} />
          <Route path="trees" element={<TreesPage />} />
          <Route path="ingest" element={<IngestPage />} />
          <Route path="agent" element={<AgentPage />} />
          <Route path="api-keys" element={<ApiKeysPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
