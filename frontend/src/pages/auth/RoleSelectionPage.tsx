import { BrainCircuit, Landmark, LockKeyhole, ShieldCheck, UserRound } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import type { UserRole } from "../../types";
import { cn } from "../../utils/cn";

const roles: Array<{ role: UserRole; title: string; description: string; Icon: typeof UserRound }> = [
  { role: "victim", title: "Victim / User", description: "Well-being check-ins, your case, support requests, and secure AI support.", Icon: UserRound },
  { role: "counsellor", title: "Counsellor", description: "Well-being requests and counselling follow-up within your district.", Icon: BrainCircuit },
  { role: "district_admin", title: "District Administrator", description: "Legal assistance, protection and case coordination for your district.", Icon: Landmark },
  { role: "state_admin", title: "State Administrator", description: "Aggregated monitoring and coordination across your state.", Icon: ShieldCheck },
  { role: "national_admin", title: "National Administrator", description: "Programme analytics and hierarchy coordination.", Icon: ShieldCheck },
];

export function RoleSelectionPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<UserRole>("victim");

  return (
    <section className="mx-auto max-w-2xl">
      <div className="text-center">
        <p className="text-[11px] font-extrabold uppercase tracking-[.16em] text-sahaya-700">Create account</p>
        <h1 className="mt-2 text-3xl font-extrabold text-slate-900">Create your SAHAYA account</h1>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">Choose what kind of account you need. Everyone signs up here with their own mobile number and password.</p>
      </div>
      <Card className="mt-7 p-5 sm:p-7">
        <div className="grid gap-2" role="radiogroup" aria-label="Account type">
          {roles.map(({ role, title, description, Icon }) => {
            const active = role === selected;
            return (
              <button
                key={role}
                type="button"
                role="radio"
                aria-checked={active}
                onClick={() => setSelected(role)}
                className={cn(
                  "flex items-start gap-3 rounded-2xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-sahaya-500",
                  active ? "border-sahaya-700 bg-sahaya-50" : "border-slate-200 bg-white hover:border-teal-300",
                )}
              >
                <span className={cn("grid h-10 w-10 shrink-0 place-items-center rounded-xl", active ? "bg-sahaya-900 text-white" : "bg-slate-100 text-sahaya-700")}>
                  <Icon size={19} />
                </span>
                <span>
                  <strong className="block text-sm text-slate-900">{title}</strong>
                  <span className="mt-1 block text-xs leading-5 text-slate-600">{description}</span>
                </span>
              </button>
            );
          })}
        </div>
        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Link to="/login" className="inline-flex min-h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-extrabold text-sahaya-900 hover:border-teal-300">Use existing account</Link>
          <Button onClick={() => navigate(`/signup?role=${selected}`)}>Continue as {roles.find((item) => item.role === selected)?.title}</Button>
        </div>
        <p className="mt-5 flex items-center justify-center gap-2 text-[11px] text-slate-500"><LockKeyhole size={13} /> Role authority is assigned and verified by the backend.</p>
      </Card>
      <p className="mt-5 text-center text-xs text-slate-500">Already registered? <Link to="/login" className="font-extrabold text-sahaya-700">Log in</Link></p>
    </section>
  );
}
