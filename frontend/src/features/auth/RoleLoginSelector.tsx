import { BrainCircuit, Landmark, ShieldCheck, UserRound } from "lucide-react";
import type { UserRole } from "../../types";

interface RoleLoginSelectorProps {
  selected: UserRole;
  onSelect: (role: UserRole) => void;
}

const roles: Array<{ role: UserRole; label: string; hint: string; Icon: typeof UserRound }> = [
  { role: "victim", label: "Victim / User", hint: "Well-being, case and support", Icon: UserRound },
  { role: "counsellor", label: "Counsellor", hint: "Assigned well-being requests", Icon: BrainCircuit },
  { role: "district_admin", label: "District", hint: "District coordination", Icon: Landmark },
  { role: "state_admin", label: "State Admin", hint: "State monitoring", Icon: ShieldCheck },
  { role: "national_admin", label: "National Admin", hint: "Programme analytics", Icon: ShieldCheck },
];

export function RoleLoginSelector({ selected, onSelect }: RoleLoginSelectorProps) {
  return (
    <section aria-labelledby="role-login-heading" className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <h2 id="role-login-heading" className="text-sm font-bold text-slate-900">Log in as</h2>
      <p className="mt-1 text-xs leading-5 text-slate-600">
        Choose your account type, then sign in with your registered mobile or email. Everyone uses the same secure sign-in below.
      </p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {roles.map(({ role, label, hint, Icon }) => {
          const active = role === selected;
          return (
            <button
              key={role}
              type="button"
              onClick={() => onSelect(role)}
              aria-pressed={active}
              title={hint}
              className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-left text-xs font-bold transition focus:outline-none focus:ring-2 focus:ring-sahaya-500 ${
                active
                  ? "border-sahaya-700 bg-sahaya-900 text-white"
                  : "border-slate-200 bg-white text-slate-800 hover:border-teal-300"
              }`}
            >
              <Icon aria-hidden="true" size={16} className={active ? "text-teal-200" : "text-sahaya-700"} />
              <span>
                <span className="block">{label}</span>
                <span className={`block text-[10px] font-semibold ${active ? "text-teal-100/80" : "text-slate-500"}`}>{hint}</span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
