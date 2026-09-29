import { BrainCircuit, Landmark, ShieldCheck, UserRound } from "lucide-react";
import type { LocalTestAccount } from "../../config/localTestAuth";

interface LocalRoleLoginSelectorProps {
  accounts: LocalTestAccount[];
  onSelect: (account: LocalTestAccount) => void;
}

const icons = {
  victim: UserRound,
  counsellor: BrainCircuit,
  district_admin: Landmark,
  state_admin: ShieldCheck,
  national_admin: ShieldCheck,
};

export function LocalRoleLoginSelector({ accounts, onSelect }: LocalRoleLoginSelectorProps) {
  if (accounts.length === 0) return null;

  return (
    <section aria-labelledby="local-role-login-heading" className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <h2 id="local-role-login-heading" className="mt-1 text-sm font-bold text-slate-900">Quick sign-in</h2>
      <p className="mt-1 text-xs leading-5 text-slate-600">
        Choose your account type to fill the sign-in form, then choose Log in securely.
      </p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {accounts.map((account) => {
          const Icon = icons[account.role];
          return (
            <button
              key={account.role}
              type="button"
              onClick={() => onSelect(account)}
              className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs font-bold text-slate-800 transition hover:border-teal-300 hover:bg-white focus:outline-none focus:ring-2 focus:ring-sahaya-500"
            >
              <Icon aria-hidden="true" size={16} className="text-sahaya-700" />
              {account.label}
            </button>
          );
        })}
      </div>
    </section>
  );
}
