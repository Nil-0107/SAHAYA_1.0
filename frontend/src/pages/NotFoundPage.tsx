import { Link } from "react-router-dom";
import { Card } from "../components/common/Card";

export function NotFoundPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-sahaya-50 p-5">
      <Card className="w-full max-w-lg p-8 text-center">
        <p className="text-[11px] font-extrabold uppercase tracking-[.16em] text-sahaya-700">404 · Page not found</p>
        <h1 className="mt-3 text-3xl font-extrabold text-slate-900">This page is not available</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">The address may be incorrect or the feature may not be configured.</p>
        <Link to="/" className="mt-5 inline-flex min-h-10 items-center justify-center rounded-xl bg-sahaya-900 px-5 py-2.5 text-sm font-extrabold text-white">Return home</Link>
      </Card>
    </main>
  );
}
