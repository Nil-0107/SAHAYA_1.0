import { ArrowLeft } from "lucide-react";
import { Link, Outlet } from "react-router-dom";

export function AuthLayout() {
  return (
    <main className="min-h-screen bg-[linear-gradient(145deg,#e8f4f2,#f7faf9)] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-6xl">
        <header className="mb-6 flex items-center justify-between sm:mb-8">
          <Link to="/" className="flex items-center gap-3 text-saathi-900 focus:outline-none focus:ring-2 focus:ring-saathi-500 focus:ring-offset-4">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-saathi-900 text-lg font-black text-white">S</span>
            <span>
              <strong className="block text-xl tracking-tight">SAATHI</strong>
              <span className="block text-[9px] font-extrabold uppercase tracking-[0.15em] text-saathi-700">Well-being support</span>
            </span>
          </Link>
          <Link to="/" className="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-extrabold text-saathi-700 transition hover:bg-white/70 focus:outline-none focus:ring-2 focus:ring-saathi-500">
            <ArrowLeft size={15} aria-hidden /> Back home
          </Link>
        </header>
        <Outlet />
      </div>
    </main>
  );
}
