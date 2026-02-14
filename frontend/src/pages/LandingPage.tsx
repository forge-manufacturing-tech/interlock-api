import Navbar from "../components/Navbar";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <div className="flex min-h-screen items-center justify-center pt-14">
        <div className="text-center">
          <h1 className="font-mono text-5xl font-bold uppercase tracking-widest text-primary">
            INTERLOCK
          </h1>
          <p className="mt-4 text-lg text-text-secondary">
            Manufacturing intelligence platform
          </p>
        </div>
      </div>
    </div>
  );
}
