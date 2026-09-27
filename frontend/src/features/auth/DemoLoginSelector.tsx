import { BrainCircuit, Landmark, ShieldCheck, UserRound } from "lucide-react";
import type { DemoLoginPersona } from "../../config/demoAuth";

interface DemoLoginSelectorProps {
  personas: DemoLoginPersona[];
  onSelect: (persona: DemoLoginPersona) => void;
}

const icons = {
  victim: UserRound,
  counsellor: BrainCircuit,
  district_admin: Landmark,
  state_admin: ShieldCheck,
  national_admin: ShieldCheck,
};

export function DemoLoginSelector({ personas, onSelect }: DemoLoginSelectorProps) {
  if (personas.length === 0) return null;

  return (
    <section aria-labelledby="demo-login-heading" className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
      <p className="text-xs font-extrabold uppercase tracking-[.16em] text-amber-800">
        Development demo
      </p>
      <h2 id="demo-login-heading" className="mt-1 text-sm font-bold text-amber-950">
        Choose a demo persona
      </h2>
      <p className="mt-1 text-xs leading-5 text-amber-900">
        Selecting a persona only fills the form. You still choose Login.
      </p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {personas.map((persona) => {
          const Icon = icons[persona.role];
          return (
            <button
              key={persona.role}
              type="button"
              onClick={() => onSelect(persona)}
              className="flex items-center gap-2 rounded-xl border border-amber-200 bg-white px-3 py-2 text-left text-xs font-bold text-amber-950 transition hover:border-amber-400 hover:bg-amber-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <Icon aria-hidden="true" size={16} />
              {persona.label}
            </button>
          );
        })}
      </div>
    </section>
  );
}
