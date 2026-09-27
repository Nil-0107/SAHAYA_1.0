export function TrendEmptyState({ label = "Trend data appears after authorised check-ins." }: { label?: string }) {
  return (
    <div className="flex min-h-36 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-5 text-center text-xs leading-5 text-slate-500">
      {label}
    </div>
  );
}
