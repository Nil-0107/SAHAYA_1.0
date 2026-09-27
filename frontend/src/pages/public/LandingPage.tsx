import { Link } from "react-router-dom";

const features = ["Periodic check-ins", "Text + voice", "Multilingual", "Human escalation", "Explainable policy"];

export function LandingPage() {
  return (
    <section className="grid min-h-screen bg-[#f5f8f8] lg:grid-cols-[1.15fr_.85fr]">
      <div className="flex items-center bg-[linear-gradient(145deg,#e8f4f2,#f7faf9)] px-6 py-12 sm:px-10 lg:px-[8vw]">
        <div className="max-w-3xl">
          <div className="flex items-center gap-3 text-saathi-900">
            <span className="grid h-11 w-11 place-items-center rounded-[13px] bg-saathi-900 text-lg font-black text-white">S</span>
            <span className="text-2xl font-black tracking-tight">SAATHI</span>
          </div>
          <p className="mt-14 text-[11px] font-extrabold uppercase tracking-[.16em] text-saathi-700">Victim well-being monitoring & support</p>
          <h1 className="mt-5 max-w-3xl text-[38px] font-black leading-[1.05] text-saathi-900 sm:text-5xl">A quiet support layer through the case journey.</h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">Periodic check-ins, longitudinal well-being monitoring, authorised support routing and human assistance — designed to work alongside the investigation, trial, rehabilitation and compensation process.</p>
          <div className="mt-7 flex flex-wrap gap-2">
            {features.map((feature) => <span key={feature} className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-extrabold text-slate-700">{feature}</span>)}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center bg-[#f5f8f8] px-5 py-12 sm:px-8">
        <div className="w-full max-w-[450px] rounded-[24px] border border-slate-200 bg-white p-7 shadow-[0_12px_35px_rgba(20,45,55,.08)] sm:p-8">
          <p className="text-[11px] font-extrabold uppercase tracking-[.16em] text-saathi-700">Secure access</p>
          <h2 className="mt-2 text-2xl font-extrabold text-slate-900">Welcome to SAATHI</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">Log in with an existing account or create a victim account to begin account-mobile verification.</p>
          <div className="mt-6 grid grid-cols-2 rounded-xl bg-[#edf4f4] p-1">
            <Link to="/login" className="rounded-lg bg-white px-4 py-2.5 text-center text-sm font-extrabold text-saathi-900 shadow-sm">Log in</Link>
            <Link to="/signup" className="rounded-lg px-4 py-2.5 text-center text-sm font-extrabold text-slate-500">Sign up</Link>
          </div>
          <div className="mt-6 grid gap-3">
            <Link to="/login" className="inline-flex min-h-10 w-full items-center justify-center rounded-xl bg-saathi-900 px-4 py-2.5 text-sm font-extrabold text-white hover:bg-saathi-700">Log in securely</Link>
            <Link to="/signup" className="inline-flex min-h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-extrabold text-saathi-900 hover:border-teal-300">Create a new account</Link>
          </div>
          <p className="mt-5 text-[11px] leading-5 text-slate-500">Account mobile verification is used for signup. Emergency contact is optional and always separate.</p>
        </div>
      </div>
    </section>
  );
}
