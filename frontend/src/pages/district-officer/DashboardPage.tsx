import { useEffect, useState } from "react";
import { Activity, Bell, BriefcaseBusiness, FileText, RefreshCw, Scale, ShieldCheck } from "lucide-react";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusPill } from "../../components/common/StatusPill";
import { EmptyState, InlineAlert, LoadingState } from "../../components/feedback/FeedbackStates";
import { authErrorMessage } from "../../utils/authErrors";
import { districtApi } from "../../services/districtApi";
import { adminApi } from "../../services/adminApi";
import type { AdminUserDetail } from "../../types/admin";
import type { DistrictDashboard } from "../../types/district";

export function DistrictDashboardPage() {
  const [data, setData] = useState<DistrictDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [users, setUsers] = useState<AdminUserDetail[]>([]);

  const load = () => {
    setLoading(true);
    setError("");
    void Promise.all([districtApi.dashboard(), adminApi.users()])
      .then(([dashboard, userRows]) => { setData(dashboard); setUsers(userRows); })
      .catch((caught) => setError(authErrorMessage(caught, "Unable to load the district dashboard.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (loading) return <LoadingState label="Loading authorised district data…" />;
  if (error || !data) return <InlineAlert>{error || "District data is unavailable."}</InlineAlert>;

  return (
    <div className="grid gap-7">
      <PageHeader eyebrow="District coordination" title="Case assistance dashboard" description="Only cases with an active district coordination assignment for your account are included. Victim identities and unassigned records are not returned." action={<div className="flex items-center gap-2"><StatusPill tone="neutral">Authorised scope</StatusPill><Button variant="ghost" onClick={load} icon={<RefreshCw size={15} />}>Refresh</Button></div>} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <AggregateCard icon={BriefcaseBusiness} label="Authorised cases" value={data.aggregate.authorized_case_count} />
        <AggregateCard icon={Scale} label="Open assistance" value={data.aggregate.open_assistance_request_count} />
        <AggregateCard icon={Activity} label="Active coordination" value={data.aggregate.active_coordination_count} />
        <AggregateCard icon={ShieldCheck} label="Protection requests" value={data.aggregate.protection_request_count} />
        <AggregateCard icon={Bell} label="Unread notifications" value={data.aggregate.unread_notification_count} />
      </section>

      <Card id="cases"><SectionHeading title="Authorised cases" description="Operational case summaries within your active district assignment scope." />{data.cases.length === 0 ? <EmptyState title="No authorised cases" description="No cases are currently assigned to this district account." /> : <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[620px] text-left text-xs"><thead className="text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="pb-3">Case ID</th><th className="pb-3">Stage</th><th className="pb-3">Status</th><th className="pb-3">Next hearing</th><th className="pb-3">Provenance</th></tr></thead><tbody className="divide-y divide-slate-100">{data.cases.map((item) => <tr key={item.id}><td className="py-3 font-extrabold text-slate-800">{item.case_number}</td><td className="py-3 text-slate-600">{item.stage}</td><td className="py-3 text-slate-600">{item.status}</td><td className="py-3 text-slate-600">{item.next_hearing ? new Date(item.next_hearing).toLocaleString() : "Not available yet"}</td><td className="py-3">{item.is_demo ? <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-extrabold text-amber-800">DEMO DATA</span> : "Operational record"}</td></tr>)}</tbody></table></div>}</Card>

      <Card id="users"><SectionHeading title="District user details" description="Victim/user profiles connected to cases in your authorised district scope." />{users.length === 0 ? <div className="mt-4"><EmptyState title="No user details" description="No user profile is currently available in this district scope." /></div> : <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[900px] text-left text-xs"><thead className="text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="pb-3">User</th><th className="pb-3">Contact</th><th className="pb-3">DOB</th><th className="pb-3">Cases</th><th className="pb-3">Support</th><th className="pb-3">Last check-in</th></tr></thead><tbody className="divide-y divide-slate-100">{users.map((item) => <tr key={item.id}><td className="py-3 font-extrabold text-slate-800">{item.full_name}</td><td className="py-3 text-slate-600">{item.phone}<br />{item.email ?? "No email"}</td><td className="py-3 text-slate-600">{item.date_of_birth ?? "Not provided"}</td><td className="py-3 text-slate-600">{item.case_count} ({item.open_case_count} open)</td><td className="py-3 text-slate-600">{item.support_request_count}</td><td className="py-3 text-slate-600">{item.last_checkin_at ? new Date(item.last_checkin_at).toLocaleString() : "None"}</td></tr>)}</tbody></table></div>}</Card>

      <Card id="coordination"><SectionHeading title="Assistance requests" description="Requests linked to the authorised cases in this dashboard." />{data.assistance_requests.length === 0 ? <EmptyState title="No assistance requests" description="No requests are linked to the currently authorised cases." /> : <div className="mt-4 grid gap-3">{data.assistance_requests.map((request) => <div key={request.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-3 text-xs"><div><p className="font-extrabold text-slate-800">{request.category.replaceAll("_", " ")} · Case {request.case_id}</p><p className="mt-1 text-[10px] text-slate-500">Updated {new Date(request.updated_at).toLocaleString()}</p></div><div className="flex items-center gap-2"><span className="rounded-full bg-white px-2 py-1 text-[10px] font-extrabold text-slate-600">{request.status}</span>{request.is_demo ? <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-extrabold text-amber-800">DEMO DATA</span> : null}</div></div>)}</div>}</Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card><SectionHeading title="Coordination information" description="Active district coordination records." />{data.coordination.length === 0 ? <EmptyState title="No coordination records" description="No active coordination assignment is available." /> : <div className="mt-4 grid gap-3">{data.coordination.map((record) => <div key={record.id} className="rounded-xl border border-slate-200 p-3 text-xs"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-extrabold text-slate-800">Case {record.case_id} · Request {record.support_request_id}</p><div className="flex items-center gap-2"><span className="text-[10px] font-extrabold text-saathi-700">{record.status}</span>{record.is_demo ? <DemoBadge /> : null}</div></div><p className="mt-2 text-slate-600">{record.reason}</p><p className="mt-1 text-[10px] text-slate-500">Assigned {new Date(record.assigned_at).toLocaleString()}</p></div>)}</div>}</Card>
        <Card><SectionHeading title="Case updates" description="District-scoped updates delivered to your account." />{data.case_updates.length === 0 ? <EmptyState title="No case updates" description="No authorised case update is available." /> : <div className="mt-4 grid gap-3">{data.case_updates.map((item) => <div key={item.id} className="rounded-xl bg-slate-50 p-3 text-xs"><div className="flex flex-wrap items-start justify-between gap-2"><p className="font-extrabold text-slate-800">{item.title}</p>{item.is_demo ? <DemoBadge /> : null}</div><p className="mt-1 leading-5 text-slate-600">{item.message}</p><p className="mt-1 text-[10px] text-slate-500">{new Date(item.created_at).toLocaleString()}</p></div>)}</div>}</Card>
      </div>

      <Card id="documents"><SectionHeading title="Notifications and document boundary" description="Notifications are shown here only when they belong to your district account." />{data.notifications.length === 0 ? <EmptyState title="No notifications" description="No district-scoped notifications are available." /> : <div className="mt-4 flex flex-wrap gap-2">{data.notifications.map((item) => <span key={item.id} className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-bold ${item.is_read ? "bg-slate-100 text-slate-600" : "bg-saathi-50 text-saathi-800"}`}>{item.title}{item.is_demo ? <span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] font-extrabold text-amber-800">DEMO DATA</span> : null}</span>)}</div>}<p className="mt-4 flex items-center gap-2 text-[11px] text-slate-500"><FileText size={14} /> Document retrieval and government/court integrations are not exposed by this dashboard.</p></Card>
    </div>
  );
}

function AggregateCard({ icon: Icon, label, value }: { icon: typeof BriefcaseBusiness; label: string; value: number }) {
  return <Card><div className="flex items-start gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-saathi-50 text-saathi-700"><Icon size={19} /></span><div><p className="text-[11px] font-bold text-slate-500">{label}</p><p className="mt-1 text-2xl font-extrabold text-slate-900">{value}</p></div></div></Card>;
}

function DemoBadge() {
  return <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-extrabold text-amber-800">DEMO DATA</span>;
}

function SectionHeading({ title, description }: { title: string; description: string }) {
  return <div><h2 className="text-lg font-extrabold text-slate-900">{title}</h2><p className="mt-1 text-sm leading-6 text-slate-500">{description}</p></div>;
}
