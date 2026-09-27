import { cn } from "../../utils/cn";

type Tone = "stable" | "watch" | "elevated" | "critical" | "neutral";

const tones: Record<Tone, string> = {
  stable: "bg-emerald-50 text-emerald-700",
  watch: "bg-amber-50 text-amber-700",
  elevated: "bg-orange-50 text-orange-700",
  critical: "bg-red-50 text-red-700",
  neutral: "bg-slate-100 text-slate-600",
};

export function StatusPill({ tone = "neutral", children }: { tone?: Tone; children: string }) {
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-1 text-[11px] font-extrabold", tones[tone])}>
      {children}
    </span>
  );
}
