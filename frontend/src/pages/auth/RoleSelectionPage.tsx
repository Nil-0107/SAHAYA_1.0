import { LockKeyhole, UserRound } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";

export function RoleSelectionPage() {
  const navigate = useNavigate();

  return (
    <section className="mx-auto max-w-2xl">
      <div className="text-center">
        <p className="text-[11px] font-extrabold uppercase tracking-[.16em] text-saathi-700">Create account</p>
        <h1 className="mt-2 text-3xl font-extrabold text-slate-900">Create your SAATHI account</h1>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">Public signup creates a Victim / User account. Staff and administrator accounts are provisioned through the secure administrative hierarchy.</p>
      </div>
      <Card className="mt-7 p-5 sm:p-7">
        <div className="flex items-start gap-3 rounded-2xl border border-saathi-200 bg-saathi-50 p-4">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-saathi-700"><UserRound size={19} /></span>
          <div>
            <strong className="block text-sm text-slate-900">Victim / User</strong>
            <span className="mt-1 block text-xs leading-5 text-slate-600">Well-being check-ins, your case, support requests, and secure AI support.</span>
          </div>
        </div>
        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Link to="/login" className="inline-flex min-h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-extrabold text-saathi-900 hover:border-teal-300">Use existing account</Link>
          <Button onClick={() => navigate("/signup")}>Continue to account details</Button>
        </div>
        <p className="mt-5 flex items-center justify-center gap-2 text-[11px] text-slate-500"><LockKeyhole size={13} /> Role authority is assigned and verified by the backend.</p>
      </Card>
      <p className="mt-5 text-center text-xs text-slate-500">Already registered? <Link to="/login" className="font-extrabold text-saathi-700">Log in</Link></p>
    </section>
  );
}
