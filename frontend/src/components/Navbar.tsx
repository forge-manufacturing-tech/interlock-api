import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AuthenticationService } from "../api";

export default function Navbar() {
  const { data: settings } = useQuery({
    queryKey: ["system-settings"],
    queryFn: () => AuthenticationService.getSystemSettingsAuthSettingsGet(),
    staleTime: 60000,
  });

  const signupEnabled = settings?.signup_enabled !== false;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex h-14 items-center justify-between border-b border-border bg-surface px-6">
      <Link to="/" className="font-mono text-lg font-bold uppercase tracking-widest text-primary no-underline">
        INTERLOCK
      </Link>
      <div className="flex items-center gap-3">
        <Link
          to="/login"
          className="rounded-md px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:text-text-primary no-underline"
        >
          LOG IN
        </Link>
        {signupEnabled && (
          <Link
            to="/signup"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90 no-underline"
          >
            GET STARTED
          </Link>
        )}
      </div>
    </nav>
  );
}
