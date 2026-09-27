import type { LucideIcon } from "lucide-react";
import { Card } from "../common/Card";

export function MetricCard({
  label,
  value,
  helper,
  icon: Icon,
}: {
  label: string;
  value: string;
  helper?: string;
  icon?: LucideIcon;
}) {
  return (
    <Card className="min-h-28">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-extrabold text-slate-900">{value}</p>
          {helper ? <p className="mt-1 text-xs text-slate-500">{helper}</p> : null}
        </div>
        {Icon ? (
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-saathi-50 text-saathi-700">
            <Icon size={18} />
          </span>
        ) : null}
      </div>
    </Card>
  );
}
