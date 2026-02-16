import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./lib/auth";
import App from "./App";
import { OpenAPI } from "./api";
import "./index.css";

// Configure API client base URL
// If VITE_API_URL is set (e.g. for production), use it.
// Otherwise default to /api which works with the local Vite proxy and Docker Nginx proxy.
OpenAPI.BASE = import.meta.env.VITE_API_URL || "/api";

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
