import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./lib/auth";
import App from "./App";
import { OpenAPI } from "./api";
import "./index.css";

// Configure API client base URL
// Use VITE_API_URL if defined, otherwise default to /api for proxy compatibility.
OpenAPI.BASE = import.meta.env.VITE_API_URL || "/api";

declare global {
  interface Window {
    OpenAPI_BASE: string;
  }
}
window.OpenAPI_BASE = OpenAPI.BASE;

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>
);
