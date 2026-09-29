import { AlertTriangle, Inbox, LoaderCircle, LockKeyhole, RefreshCw, ServerOff } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "../common/Button";

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex min-h-40 items-center justify-center gap-2 text-sm font-bold text-slate-500">
      <LoaderCircle className="animate-spin text-sahaya-700" size={18} /> {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 shrink-0" size={18} />
        <div>
          <p className="font-extrabold">Something went wrong</p>
          <p className="mt-1 leading-6">{message}</p>
          {onRetry ? (
            <Button variant="secondary" className="mt-3" onClick={onRetry} icon={<RefreshCw size={15} />}>
              Try again
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
      <span className="mx-auto grid h-11 w-11 place-items-center rounded-2xl bg-white text-sahaya-700 shadow-sm">
        <Inbox size={20} />
      </span>
      <h3 className="mt-3 text-sm font-extrabold text-slate-800">{title}</h3>
      <p className="mx-auto mt-1 max-w-md text-xs leading-5 text-slate-500">{description}</p>
      {action ? <div className="mt-4 flex justify-center">{action}</div> : null}
    </div>
  );
}

export function ForbiddenState() {
  return (
    <div className="rounded-card border border-amber-200 bg-amber-50 p-6 text-center">
      <span className="mx-auto grid h-11 w-11 place-items-center rounded-2xl bg-white text-amber-700 shadow-sm">
        <LockKeyhole size={20} />
      </span>
      <h2 className="mt-3 text-lg font-extrabold text-slate-900">Access restricted</h2>
      <p className="mt-1 text-sm text-slate-600">You do not have access to this information.</p>
      <Button variant="secondary" className="mt-4" onClick={() => window.location.assign("/")}>Return to SAHAYA</Button>
    </div>
  );
}

export function NotConfiguredState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-card border border-slate-200 bg-white p-7 text-center shadow-card">
      <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-sahaya-50 text-sahaya-700">
        <ServerOff size={22} />
      </span>
      <h2 className="mt-4 text-lg font-extrabold text-slate-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}

export function InlineAlert({ children, tone = "error" }: { children: ReactNode; tone?: "error" | "success" | "info" }) {
  const style = {
    error: "border-red-200 bg-red-50 text-red-700",
    success: "border-emerald-200 bg-emerald-50 text-emerald-700",
    info: "border-teal-200 bg-sahaya-50 text-sahaya-700",
  }[tone];
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`rounded-xl border px-3 py-2 text-xs font-bold ${style}`}
    >
      {children}
    </div>
  );
}
