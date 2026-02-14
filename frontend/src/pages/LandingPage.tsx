import { Link } from "react-router-dom";
import Navbar from "@/components/Navbar";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface">
      <Navbar />

      <section className="relative flex min-h-screen items-center justify-center px-6 pt-14">
        <div
          className="pointer-events-none absolute inset-0 flex items-center justify-center"
          aria-hidden="true"
        >
          <div className="h-[600px] w-[600px] rounded-full bg-primary/5 blur-[120px]" />
        </div>

        <div className="relative z-10 mx-auto max-w-6xl text-center">
          <span className="mb-8 inline-block rounded-full border border-primary px-4 py-1.5 font-mono text-xs uppercase tracking-widest text-primary">
            THE SOFTWARE-ENABLED SOLUTION
          </span>

          <h1 className="font-mono text-6xl font-bold uppercase leading-none text-text-primary md:text-8xl">
            ACCELERATE TECH TRANSFER
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-text-secondary">
            Bridging the gap between engineering design and manufacturing production.
          </p>

          <p className="mx-auto mt-4 max-w-2xl font-mono text-sm text-text-muted">
            No behavior change required. We ingest your existing PDFs, Excel BOMs, and CAD packs and turn them into ERP-ready data.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              to="/signup"
              className="rounded-md bg-primary px-8 py-3 font-mono text-sm font-semibold uppercase tracking-wider text-white no-underline transition-colors hover:bg-primary/90"
            >
              INITIALIZE TRANSFER
            </Link>
            <a
              href="#how-it-works"
              className="rounded-md border border-border px-8 py-3 font-mono text-sm font-semibold uppercase tracking-wider text-text-primary no-underline transition-colors hover:border-text-muted"
            >
              VIEW SOLUTIONS
            </a>
          </div>
        </div>
      </section>

      <section className="px-6 py-24">
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
      </section>

      <section id="how-it-works" className="px-6 py-24">
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
      </section>

      <section className="px-6 py-24">
        <div className="mx-auto max-w-6xl text-center">
          <h2 className="font-mono text-3xl font-bold text-text-primary md:text-4xl">
            Ready to sync?
          </h2>
          <p className="mt-4 text-lg text-text-secondary">
            Stop interpreting. Start manufacturing.
          </p>
          <Link
            to="/signup"
            className="mt-8 inline-block rounded-md bg-primary px-8 py-3 font-mono text-sm font-semibold uppercase tracking-wider text-white no-underline transition-colors hover:bg-primary/90"
          >
            INITIALIZE TRANSFER
          </Link>
        </div>
      </section>

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
