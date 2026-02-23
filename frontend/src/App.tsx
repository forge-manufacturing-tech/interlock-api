import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { RequireAuth } from "./lib/auth";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const DashboardLayout = lazy(() => import("./components/DashboardLayout"));
const PartsPage = lazy(() => import("./pages/PartsPage"));
const PartVisualizerPage = lazy(() => import("./pages/PartVisualizerPage"));

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
          <Route path="parts/:partId" element={<PartVisualizerPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
