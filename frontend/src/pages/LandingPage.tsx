import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AuthenticationService } from "../api";
import Navbar from "@/components/Navbar";

export default function LandingPage() {
  const { data: settings } = useQuery({
    queryKey: ["system-settings"],
    queryFn: () => AuthenticationService.getSystemSettingsAuthSettingsGet(),
    staleTime: 60000,
  });

  const signupEnabled = settings?.signup_enabled !== false;

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />

      <section className="relative flex min-h-screen items-center justify-center px-6 pt-14 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 flex items-center justify-center"
          aria-hidden="true"
        >
          <div className="h-[600px] w-[600px] rounded-full bg-primary/5 blur-[120px]" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="relative z-10 mx-auto max-w-6xl text-center"
        >
          <div className="mb-8 inline-flex items-center rounded-full border border-primary/30 bg-primary/5 px-3 py-1">
            <span className="font-mono text-[10px] font-medium uppercase tracking-[0.2em] text-primary">
              THE SOFTWARE-ENABLED SOLUTION
            </span>
          </div>

          <h1 className="font-mono text-6xl font-bold uppercase leading-tight text-primary md:text-8xl lg:text-9xl">
            ACCELERATE <br /> TECH TRANSFER
          </h1>

          <p className="mx-auto mt-8 max-w-2xl text-lg text-text-secondary md:text-xl">
            Bridging the gap between engineering design and manufacturing production.
          </p>

          <p className="mx-auto mt-4 max-w-2xl font-mono text-sm text-text-muted">
            No behavior change required. We ingest your existing PDFs, Excel BOMs, and CAD packs and turn them into ERP-ready data.
          </p>

          <div className="mt-12 flex flex-col items-center justify-center gap-6 sm:flex-row">
            {signupEnabled ? (
              <Link
                to="/signup"
                className="rounded-md border border-primary bg-surface px-10 py-4 font-mono text-xs font-semibold uppercase tracking-[0.15em] text-primary transition-all hover:bg-primary/10"
              >
                INITIALIZE TRANSFER
              </Link>
            ) : (
              <Link
                to="/login"
                className="rounded-md border border-primary bg-surface px-10 py-4 font-mono text-xs font-semibold uppercase tracking-[0.15em] text-primary transition-all hover:bg-primary/10"
              >
                SIGN IN
              </Link>
            )}
            <a
              href="#how-it-works"
              className="rounded-md border border-white/10 bg-surface px-10 py-4 font-mono text-xs font-semibold uppercase tracking-[0.15em] text-text-secondary transition-all hover:border-white/20 hover:text-text-primary"
            >
              VIEW SOLUTIONS
            </a>
          </div>
        </motion.div>
      </section>

      <motion.section
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="px-6 py-24"
      >
        <div className="mx-auto max-w-6xl">
          <p className="text-center font-mono text-xs uppercase tracking-widest text-text-muted">
            WHY THE OLD WAY IS BROKEN
          </p>
          <h2 className="mt-4 text-center font-mono text-3xl font-bold uppercase tracking-wide text-text-primary md:text-4xl">
            THE COST OF MANUAL TRANSFER
          </h2>

          <div className="mt-16 grid gap-6 md:grid-cols-3">
            <div className="rounded-lg border border-border bg-surface-light p-8 text-center">
              <p className="font-mono text-4xl font-bold text-primary">6-12</p>
              <p className="mt-2 font-mono text-xs uppercase tracking-wider text-text-muted">
                MONTHS
              </p>
              <p className="mt-4 text-sm text-text-secondary">
                Current timeline for tech transfer per product line
              </p>
            </div>

            <div className="rounded-lg border border-border bg-surface-light p-8 text-center">
              <p className="font-mono text-4xl font-bold text-primary">8,500</p>
              <p className="mt-2 font-mono text-xs uppercase tracking-wider text-text-muted">
                PAGES
              </p>
              <p className="mt-4 text-sm text-text-secondary">
                Average volume of documentation teams must reconcile
              </p>
            </div>

            <div className="rounded-lg border border-border bg-surface-light p-8 text-center">
              <p className="font-mono text-4xl font-bold text-primary">30%</p>
              <p className="mt-2 font-mono text-xs uppercase tracking-wider text-text-muted">
                FAILURE RATE
              </p>
              <p className="mt-4 text-sm text-text-secondary">
                Of pilot runs fail due to manual transcription errors
              </p>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section
        id="how-it-works"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="px-6 py-24"
      >
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center font-mono text-3xl font-bold text-text-primary md:text-4xl">
            From documents to production
          </h2>

          <div className="mt-16 space-y-6">
            <div className="flex items-start gap-8 rounded-lg border border-border bg-surface-light p-8">
              <span className="font-mono text-4xl font-bold text-primary">01</span>
              <div>
                <h3 className="font-mono text-xl font-semibold text-text-primary">Ingest</h3>
                <p className="mt-2 text-text-secondary">
                  CAD files, engineering notes, BOMs — we understand your existing data.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-8 rounded-lg border border-border bg-surface-light p-8">
              <span className="font-mono text-4xl font-bold text-primary">02</span>
              <div>
                <h3 className="font-mono text-xl font-semibold text-text-primary">Structure</h3>
                <p className="mt-2 text-text-secondary">
                  An integrated knowledge graph that connects every part, spec, and requirement.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-8 rounded-lg border border-border bg-surface-light p-8">
              <span className="font-mono text-4xl font-bold text-primary">03</span>
              <div>
                <h3 className="font-mono text-xl font-semibold text-text-primary">Generate</h3>
                <p className="mt-2 text-text-secondary">
                  Work instructions, regulatory docs, and ERP-ready outputs — automatically.
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="px-6 py-24 border-t border-border/50"
      >
        <div className="mx-auto max-w-6xl">
          <p className="text-center font-mono text-xs uppercase tracking-widest text-text-muted">
            FOUNDING TEAM
          </p>
          <h2 className="mt-4 text-center font-mono text-3xl font-bold uppercase tracking-wide text-text-primary md:text-4xl">
            Architects of the new standard
          </h2>

          <div className="mt-16 grid gap-12 md:grid-cols-2">
            <div className="text-center">
              <div className="mx-auto mb-6 h-48 w-48 overflow-hidden rounded-full border border-primary/20 bg-surface-light grayscale hover:grayscale-0 transition-all duration-500">
                <img
                  src="/assets/team/tyler.png"
                  alt="Tyler Mangini"
                  className="h-full w-full object-cover"
                />
              </div>
              <h3 className="font-mono text-xl font-bold text-text-primary">Tyler Mangini</h3>
              <p className="mt-2 font-mono text-xs uppercase tracking-wider text-primary">Co-Founder</p>
            </div>

            <div className="text-center">
              <div className="mx-auto mb-6 h-48 w-48 overflow-hidden rounded-full border border-primary/20 bg-surface-light grayscale hover:grayscale-0 transition-all duration-500">
                <img
                  src="/assets/team/arshaan.png"
                  alt="Arshaan Ali"
                  className="h-full w-full object-cover"
                />
              </div>
              <h3 className="font-mono text-xl font-bold text-text-primary">Arshaan Ali</h3>
              <p className="mt-2 font-mono text-xs uppercase tracking-wider text-primary">Co-Founder</p>
            </div>

          </div>
        </div>
      </motion.section>

      <motion.section
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="px-6 py-24"
      >
        <div className="mx-auto max-w-6xl text-center">
          <h2 className="font-mono text-3xl font-bold text-text-primary md:text-4xl">
            Ready to sync?
          </h2>
          <p className="mt-4 text-lg text-text-secondary">
            Stop interpreting. Start manufacturing.
          </p>
          {signupEnabled ? (
            <Link
              to="/signup"
              className="mt-8 inline-block rounded-md border border-primary bg-surface px-10 py-4 font-mono text-xs font-semibold uppercase tracking-[0.15em] text-primary transition-all hover:bg-primary/10"
            >
              INITIALIZE TRANSFER
            </Link>
          ) : (
            <Link
              to="/login"
              className="mt-8 inline-block rounded-md border border-primary bg-surface px-10 py-4 font-mono text-xs font-semibold uppercase tracking-[0.15em] text-primary transition-all hover:bg-primary/10"
            >
              SIGN IN
            </Link>
          )}
        </div>
      </motion.section>

      <footer className="border-t border-border px-6 py-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <span className="font-mono text-sm font-bold uppercase tracking-widest text-primary">
            INTERLOCK
          </span>
          <p className="text-xs text-text-muted">
            &copy; {new Date().getFullYear()} Interlock. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
