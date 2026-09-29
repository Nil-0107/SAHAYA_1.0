import { useEffect, useState } from "react";
import { BarChart3, ClipboardList, Layers3, RefreshCw, ShieldCheck } from "lucide-react";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { PageHeader } from "../../components/common/PageHeader";
import { EmptyState, InlineAlert, LoadingState } from "../../components/feedback/FeedbackStates";
import { adminApi } from "../../services/adminApi";
import { notificationApi, type NotificationTargetDetail } from "../../services/notificationApi";
import type { AdministrativePriority, AdminDashboard, AdminPriorityQueueItem, AdminUserDetail } from "../../types/admin";
import { authErrorMessage } from "../../utils/authErrors";

export function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [users, setUsers] = useState<AdminUserDetail[]>([]);
  const [usersError, setUsersError] = useState("");
  const [notificationTarget, setNotificationTarget] = useState<NotificationTargetDetail | null>(null);
  const [notificationLoading, setNotificationLoading] = useState(false);
  const [selectedPriority, setSelectedPriority] = useState<AdminPriorityQueueItem | null>(null);
  const [priorityLoading, setPriorityLoading] = useState(false);

  const load = () => {
    setLoading(true);
    setError("");
    void adminApi.dashboard()
      .then(setData)
      .catch((caught) => setError(authErrorMessage(caught, "Unable to load the administrator dashboard.")))
      .finally(() => setLoading(false));
    void adminApi.users()
      .then(setUsers)
      .catch((caught) => setUsersError(authErrorMessage(caught, "Unable to load user details.")));
  };

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 15000);
    return () => window.clearInterval(timer);
  }, []);

  const openNotification = async (id: number) => {
    setNotificationLoading(true);
    setError("");
    try {
      await notificationApi.markRead(id);
      setNotificationTarget(await notificationApi.targetDetails(id));
      setData((current) => current ? { ...current, notifications: current.notifications.map((item) => item.id === id ? { ...item, is_read: true, read_at: item.read_at ?? new Date().toISOString() } : item) } : current);
    } catch (caught) {
      setError(authErrorMessage(caught, "The linked notification details could not be loaded."));
    } finally {
      setNotificationLoading(false);
    }
  };

  const openPriority = async (caseId: number) => {
    setPriorityLoading(true);
    setError("");
    try {
      setSelectedPriority(await adminApi.casePriority(caseId));
    } catch (caught) {
      setError(authErrorMessage(caught, "The selected case priority could not be loaded."));
    } finally {
      setPriorityLoading(false);
    }
  };

  if (loading) return <LoadingState label="Loading aggregate programme data…" />;
  if (error || !data) return <InlineAlert>{error || "Administrator data is unavailable."}</InlineAlert>;

  return (
    <div className="grid gap-7">
      <PageHeader
        eyebrow="Aggregate programme workspace"
        title="Programme overview"
        description="Live operational view. Counts, queues, notifications and user directories are sourced from authorised backend data."
        action={<Button variant="ghost" onClick={load} icon={<RefreshCw size={15} />}>Refresh</Button>}
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <AggregateCard icon={ShieldCheck} label="Active cases" value={data.aggregate.active_case_count} detail={`${data.aggregate.total_case_count} total cases`} />
        <AggregateCard icon={ClipboardList} label="Open support requests" value={data.aggregate.open_support_request_count} detail={`${data.aggregate.total_support_request_count} total requests`} />
        <AggregateCard icon={Layers3} label="Active assignments" value={data.aggregate.active_assignment_count} detail={`${data.aggregate.district_count} districts represented`} />
        <AggregateCard icon={BarChart3} label="Check-ins recorded" value={data.aggregate.total_checkin_count} detail={`${data.aggregate.active_user_count} active accounts`} />
      </section>

      <Card id="districts" className="scroll-mt-24">
        <SectionHeading title="District analytics" description="Operational counts grouped by the victim's configured district; no profile or contact information is returned." />
        {data.district_analytics.length === 0 ? <EmptyState title="No district data" description="No district-level operational records are available." /> : <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[680px] text-left text-xs"><thead className="text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="pb-3">District</th><th className="pb-3">Cases</th><th className="pb-3">Open support</th><th className="pb-3">High priority</th><th className="pb-3">Active assignments</th></tr></thead><tbody className="divide-y divide-slate-100">{data.district_analytics.map((item) => <tr key={item.district}><td className="py-3 font-extrabold text-slate-800">{item.district}</td><td className="py-3 text-slate-600">{item.case_count} <span className="text-slate-400">({item.active_case_count} active)</span></td><td className="py-3 text-slate-600">{item.open_support_request_count} <span className="text-slate-400">of {item.support_request_count}</span></td><td className="py-3 text-slate-600">{item.high_priority_request_count}</td><td className="py-3 text-slate-600">{item.active_assignment_count}</td></tr>)}</tbody></table></div>}
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card id="support-counts" className="scroll-mt-24">
          <SectionHeading title="Support request counts" description="Counts are calculated from the support request table, not frontend constants." />
          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <CountList title="By type" values={data.support_request_counts.by_type} />
            <CountList title="By status" values={data.support_request_counts.by_status} />
          </div>
        </Card>
        <Card id="trends" className="scroll-mt-24">
          <SectionHeading title="Escalation trends" description="High-priority support requests grouped by their actual creation date." />
          <TrendChart points={data.escalation_trends} />
        </Card>
      </div>

      <Card id="queue" className="scroll-mt-24">
        <SectionHeading title="Priority queue" description="Open high-priority support requests. Case references are operational identifiers only; free text and victim identity are omitted." />
        {data.priority_queue.length === 0 ? <EmptyState title="No priority records" description="No case-level administrative priority records are currently available." /> : <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[900px] text-left text-xs"><thead className="text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="pb-3">Case</th><th className="pb-3">District</th><th className="pb-3">Category</th><th className="pb-3">Routing</th><th className="pb-3">Explanation</th></tr></thead><tbody className="divide-y divide-slate-100">{data.priority_queue.map((item) => <tr key={item.case_id} role="button" tabIndex={0} className="cursor-pointer hover:bg-slate-50 focus:bg-slate-50 focus:outline-none" onClick={() => void openPriority(item.case_id)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); void openPriority(item.case_id); } }} title="Open case priority details"><td className="py-3 font-extrabold text-slate-800">{item.case_number}</td><td className="py-3 text-slate-600">{item.district}</td><td className="py-3 text-slate-600">{item.category.replaceAll("_", " ")}</td><td className="py-3"><PriorityBadge priority={item.priority} /></td><td className="max-w-sm py-3 leading-5 text-slate-600">{item.explanation}</td></tr>)}</tbody></table></div>}
      </Card>


      <Card id="users" className="scroll-mt-24">
        <SectionHeading title="Authorised user details" description="Victim/user details are shown only inside the authenticated administrator's geographic scope." />
        {usersError ? <div className="mt-4"><InlineAlert>{usersError}</InlineAlert></div> : null}
        {!usersError && users.length === 0 ? <div className="mt-4"><EmptyState title="No user records" description="No user profile is currently available in your authorised scope." /></div> : null}
        {users.length > 0 ? <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[1050px] text-left text-xs"><thead className="text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="pb-3">User</th><th className="pb-3">Contact</th><th className="pb-3">DOB</th><th className="pb-3">Location</th><th className="pb-3">Cases</th><th className="pb-3">Support</th><th className="pb-3">Last check-in</th></tr></thead><tbody className="divide-y divide-slate-100">{users.map((item) => <tr key={item.id}><td className="py-3"><p className="font-extrabold text-slate-800">{item.full_name}</p><p className="text-[10px] text-slate-500">{item.display_name} · {item.status}</p></td><td className="py-3 text-slate-600">{item.phone}<br />{item.email ?? "No email"}</td><td className="py-3 text-slate-600">{item.date_of_birth ?? "Not provided"}</td><td className="py-3 text-slate-600">{item.district_name ?? "District not assigned"}{item.state_name ? ` · ${item.state_name}` : ""}</td><td className="py-3 font-bold text-slate-700">{item.case_count} ({item.open_case_count} open)</td><td className="py-3 text-slate-600">{item.support_request_count}</td><td className="py-3 text-slate-600">{item.last_checkin_at ? new Date(item.last_checkin_at).toLocaleString() : "None"}</td></tr>)}</tbody></table></div> : null}
      </Card>
      <Card id="notifications">
        <SectionHeading title="Notifications" description="Only notifications addressed to the authenticated administrator account are shown." />
        {data.notifications.length === 0 ? (
          <EmptyState title="No notifications" description="No administrator notifications are available." />
        ) : (
          <div className="mt-4 grid gap-3">
            {data.notifications.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => void openNotification(item.id)}
                className="block w-full rounded-xl bg-slate-50 p-3 text-left hover:bg-slate-100"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="text-sm font-extrabold text-slate-800">{item.title}</p>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-1 text-[10px] font-extrabold ${
                        item.is_read ? "bg-slate-200 text-slate-600" : "bg-sahaya-100 text-sahaya-800"
                      }`}
                    >
                      {item.is_read ? "Read" : "Unread"}
                    </span>
                  </div>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600">{item.message}</p>
                <p className="mt-1 text-[10px] text-slate-500">
                  {new Date(item.created_at).toLocaleString()}
                </p>
              </button>
            ))}
          </div>
        )}
      </Card>
      <Card id="audit" className="scroll-mt-24">
        <SectionHeading title="Audit information" description="Authorised, minimised administrative and operational audit events returned by the backend." />
        {data.audit_entries.length === 0 ? <div className="mt-4"><EmptyState title="No audit events" description="No audit events are available within your scope." /></div> : <div className="mt-4 grid gap-2">{data.audit_entries.map((entry) => <div key={entry.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs"><div><p className="font-extrabold text-slate-800">{entry.action.replaceAll("_", " ")}</p><p className="mt-1 text-[10px] text-slate-500">{entry.resource_type} · {entry.resource_id}</p></div><div className="text-right"><p className="text-[10px] text-slate-500">{new Date(entry.created_at).toLocaleString()}</p></div></div>)}</div>}
      </Card>
      <Card id="settings" className="scroll-mt-24">
        <SectionHeading title="Dashboard settings" description="The administrator dashboard always displays authorised operational records from the backend." />
        <div className="mt-4 rounded-2xl bg-slate-50 p-4"><p className="text-sm font-extrabold text-slate-900">Operational data view</p><p className="mt-1 text-xs leading-5 text-slate-500">Only authorised operational records are displayed. Use Refresh to request the latest backend state.</p></div>
      </Card>
      {notificationLoading || priorityLoading ? <div className="fixed inset-0 z-40 grid place-items-center bg-slate-950/25 p-4"><div className="rounded-2xl bg-white px-5 py-4 text-sm font-bold shadow-xl">Loading details…</div></div> : null}
      {notificationTarget ? <DetailModal title="Help-seeking user" onClose={() => setNotificationTarget(null)}><div className="grid gap-3 sm:grid-cols-2"><Info label="Name" value={notificationTarget.user.full_name} /><Info label="Contact" value={notificationTarget.user.email ?? notificationTarget.user.phone} /><Info label="Location" value={[notificationTarget.user.district_name, notificationTarget.user.state_name].filter(Boolean).join(" · ") || "Not assigned"} /><Info label="Date of birth" value={notificationTarget.user.date_of_birth ?? "Not provided"} /></div>{notificationTarget.case ? <div className="mt-4 rounded-2xl bg-slate-50 p-4"><p className="text-sm font-extrabold text-slate-900">Case {notificationTarget.case.case_number}</p><p className="mt-1 text-xs text-slate-500">{notificationTarget.case.category} · {notificationTarget.case.status} · {notificationTarget.case.stage}</p><p className="mt-3 text-xs text-slate-600">{notificationTarget.case.summary ?? "No case summary is available."}</p></div> : <p className="mt-4 text-sm text-slate-500">This notification has no case details.</p>}</DetailModal> : null}
      {selectedPriority ? <DetailModal title={`Case ${selectedPriority.case_number}`} onClose={() => setSelectedPriority(null)}><div className="grid gap-3 sm:grid-cols-2"><Info label="District" value={selectedPriority.district} /><Info label="Category" value={selectedPriority.category.replaceAll("_", " ")} /><Info label="Priority" value={selectedPriority.priority} /><Info label="Explanation" value={selectedPriority.explanation} /></div></DetailModal> : null}
    </div>
  );
}

function AggregateCard({ icon: Icon, label, value, detail }: { icon: typeof BarChart3; label: string; value: number; detail: string }) {
  return <Card><div className="flex items-start gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-sahaya-50 text-sahaya-700"><Icon size={19} /></span><div><p className="text-[11px] font-bold text-slate-500">{label}</p><p className="mt-1 text-2xl font-extrabold text-slate-900">{value}</p><p className="mt-1 text-[10px] text-slate-500">{detail}</p></div></div></Card>;
}

function SectionHeading({ title, description }: { title: string; description: string }) {
  return <div><h2 className="text-lg font-extrabold text-slate-900">{title}</h2><p className="mt-1 text-sm leading-6 text-slate-500">{description}</p></div>;
}

function DetailModal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-4" onClick={onClose}><section className="max-h-[88vh] w-full max-w-2xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl" onClick={(event) => event.stopPropagation()}><div className="flex items-start justify-between gap-4"><h2 className="text-xl font-extrabold text-slate-900">{title}</h2><button type="button" className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-bold" onClick={onClose}>Close</button></div><div className="mt-5">{children}</div></section></div>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl bg-slate-50 p-3"><p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p><p className="mt-1 text-sm font-bold text-slate-800">{value}</p></div>;
}

function CountList({ title, values }: { title: string; values: AdminDashboard["support_request_counts"]["by_type"] }) {
  return <div><p className="text-xs font-extrabold uppercase tracking-wider text-slate-500">{title}</p><div className="mt-3 grid gap-2">{values.length === 0 ? <p className="text-sm text-slate-500">No records</p> : values.map((item) => <div key={item.label} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-sm"><span className="font-bold capitalize text-slate-700">{item.label.replaceAll("_", " ")}</span><span className="font-extrabold text-slate-900">{item.count}</span></div>)}</div></div>;
}

function PriorityBadge({ priority }: { priority: AdministrativePriority }) {
  const style = priority === "HIGH" ? "bg-red-100 text-red-800" : priority === "REVIEW" ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700";
  return <span className={`rounded-full px-2 py-1 text-[10px] font-extrabold ${style}`}>{priority}</span>;
}

function TrendChart({ points }: { points: AdminDashboard["escalation_trends"] }) {
  if (!points.length) return <EmptyState title="No escalation trend data" description="No high-priority requests are available in the selected data view." />;
  const max = Math.max(1, ...points.map((p) => p.request_count));
  const width = 640; const height = 180; const pad = 20;
  const path = points.map((p, i) => {
    const x = pad + (i * (width - pad * 2)) / Math.max(1, points.length - 1);
    const y = height - pad - (p.request_count / max) * (height - pad * 2);
    return `${i === 0 ? "M" : "L"} ${x} ${y}`;
  }).join(" ");
  return <div className="mt-4">
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-slate-50 p-3">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-48 min-w-[620px] w-full" role="img" aria-label="Escalation request trend">
        <line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="currentColor" className="text-slate-300" />
        <path d={path} fill="none" stroke="currentColor" strokeWidth="3" className="text-sahaya-700" />
        {points.map((p, i) => { const x = pad + (i * (width-pad*2))/Math.max(1, points.length-1); const y = height-pad-(p.request_count/max)*(height-pad*2); return <circle key={p.date} cx={x} cy={y} r="4" className="fill-sahaya-700" />; })}
      </svg>
    </div>
    <div className="mt-2 grid gap-2 sm:grid-cols-3">{points.slice(-3).map((p) => <div key={p.date} className="rounded-xl border border-slate-200 p-3 text-xs"><p className="font-bold text-slate-500">{new Date(`${p.date}T00:00:00`).toLocaleDateString()}</p><p className="mt-1 font-extrabold text-slate-900">{p.request_count} escalations</p><p className="text-slate-500">{p.open_count} open · {p.resolved_count} resolved</p></div>)}</div>
  </div>;
}
