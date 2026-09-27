import { useEffect, useState } from "react";
import { Bell, ClipboardCheck, HeartHandshake, Inbox, RefreshCw, ShieldCheck } from "lucide-react";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusPill } from "../../components/common/StatusPill";
import { EmptyState, InlineAlert, LoadingState } from "../../components/feedback/FeedbackStates";
import { counsellorApi } from "../../services/counsellorApi";
import { supportApi } from "../../services/supportApi";
import type { CounsellorDashboard, CounsellorUserDetail } from "../../types/counsellor";
import { authErrorMessage } from "../../utils/authErrors";

export function CounsellorDashboardPage() {
  const [data, setData] = useState<CounsellorDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionNotes, setActionNotes] = useState<Record<number, string>>({});
  const [actionSaving, setActionSaving] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
  const [users, setUsers] = useState<CounsellorUserDetail[]>([]);

  const load = () => {
    setLoading(true);
    setError("");
    void Promise.all([counsellorApi.dashboard(), counsellorApi.users()])
      .then(([dashboard, assignedUsers]) => { setData(dashboard); setUsers(assignedUsers); })
      .catch((caught) => setError(authErrorMessage(caught, "Unable to load the counsellor dashboard.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const saveAction = async (requestId: number) => {
    const notes = actionNotes[requestId]?.trim();
    if (!notes) {
      setActionError("Enter a support action note before saving.");
      return;
    }
    setActionSaving(requestId);
    setActionError("");
    try {
      await supportApi.createAction(requestId, { action: "follow_up", notes, request_status: "in_progress" });
      setActionNotes((current) => ({ ...current, [requestId]: "" }));
      load();
    } catch (caught) {
      setActionError(authErrorMessage(caught, "Unable to save the support action."));
    } finally {
      setActionSaving(null);
    }
  };

  if (loading) return <LoadingState label="Loading assigned counselling records…" />;
  if (error || !data) return <InlineAlert>{error || "Counsellor data is unavailable."}</InlineAlert>;

  return (
    <div className="grid gap-7">
      <PageHeader
        eyebrow="Authorised care workspace"
        title="Well-being care dashboard"
        description="Only active wellbeing-counsellor assignments for your account are shown. This workspace does not provide arbitrary victim lookup or another counsellor's assignment access."
        action={
          <div className="flex items-center gap-2">
            <StatusPill tone="neutral">Authorised scope</StatusPill>
            <Button variant="ghost" onClick={load} icon={<RefreshCw size={15} />}>Refresh</Button>
          </div>
        }
      />

      {actionError ? <InlineAlert>{actionError}</InlineAlert> : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <AggregateCard icon={Inbox} label="Assigned requests" value={data.aggregate.assigned_request_count} />
        <AggregateCard icon={HeartHandshake} label="Open follow-ups" value={data.aggregate.open_follow_up_count} />
        <AggregateCard icon={ClipboardCheck} label="Support actions" value={data.aggregate.support_action_count} />
        <AggregateCard icon={ShieldCheck} label="Resolved requests" value={data.aggregate.resolved_request_count} />
        <AggregateCard icon={Bell} label="Unread notifications" value={data.aggregate.unread_notification_count} />
      </section>

      <Card id="users" className="scroll-mt-24">
        <SectionHeading title="People assigned to you" description="Only users connected to your active counsellor assignments are visible here." />
        {users.length === 0 ? <div className="mt-4"><EmptyState title="No assigned people" description="When a wellbeing support request is assigned to you, the user's authorised details appear here." /></div> : <div className="mt-4 grid gap-3">{users.map((item) => <div key={`${item.id}-${item.support_request_id}`} className="rounded-2xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-sm font-extrabold text-slate-900">{item.full_name}</p><p className="mt-1 text-xs text-slate-500">{item.email ?? item.phone} · Case {item.case_number}</p></div><span className="rounded-full bg-saathi-50 px-2.5 py-1 text-[10px] font-extrabold text-saathi-800">{item.support_status}</span></div><div className="mt-3 grid gap-2 text-xs sm:grid-cols-3"><span><b>DOB:</b> {item.date_of_birth ?? "Not provided"}</span><span><b>District:</b> {item.district_name ?? "Not assigned"}</span><span><b>Last check-in:</b> {item.last_checkin_at ? new Date(item.last_checkin_at).toLocaleString() : "None"}</span></div></div>)}</div>}
      </Card>

      <Card id="assigned" className="scroll-mt-24">
        <SectionHeading title="Assigned well-being requests" description="Requests currently assigned to your counsellor account." />
        {data.support_requests.length === 0 ? (
          <EmptyState title="No assigned requests" description="Requests appear here after an active wellbeing-counsellor assignment is created." />
        ) : (
          <div className="mt-4 grid gap-3">
            {data.support_requests.map((request) => (
              <div key={request.id} className="rounded-2xl border border-slate-200 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-extrabold text-slate-900">Request #{request.id} · Case {request.case_id}</p>
                    <p className="mt-1 text-xs text-slate-500">Created {new Date(request.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-saathi-50 px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wide text-saathi-800">{request.category.replaceAll("_", " ")}</span>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-extrabold text-slate-600">{request.status}</span>
                    {request.is_demo ? <DemoBadge /> : null}
                  </div>
                </div>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-600">{request.details}</p>
                <p className="mt-3 text-[11px] font-bold text-slate-500">Priority: {request.priority}</p>
                <div className="mt-4 border-t border-slate-100 pt-3"><label className="text-xs font-extrabold text-slate-700" htmlFor={`action-${request.id}`}>Record follow-up action</label><textarea id={`action-${request.id}`} value={actionNotes[request.id] ?? ""} onChange={(event) => setActionNotes((current) => ({ ...current, [request.id]: event.target.value }))} className="mt-2 min-h-20 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-saathi-500 focus:ring-2 focus:ring-teal-100" placeholder="Record an authorised support action…" /><div className="mt-2 flex justify-end"><Button type="button" variant="secondary" loading={actionSaving === request.id} onClick={() => void saveAction(request.id)}>Save action</Button></div></div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card id="follow-up" className="scroll-mt-24">
          <SectionHeading title="Follow-ups" description="Recorded support actions within your assigned request scope." />
          {data.follow_ups.length === 0 ? (
            <EmptyState title="No follow-ups" description="No support action has been recorded for your assigned requests." />
          ) : (
            <ActionList actions={data.follow_ups} />
          )}
        </Card>
        <Card id="actions" className="scroll-mt-24">
          <SectionHeading title="Support actions" description="The latest actions recorded by your counsellor account." />
          {data.support_actions.length === 0 ? (
            <EmptyState title="No support actions" description="Your recorded support actions appear here." />
          ) : (
            <ActionList actions={data.support_actions} />
          )}
        </Card>
      </div>

      <Card>
        <SectionHeading title="Notifications" description="Notifications are included only when they belong to your counsellor account and assigned case scope." />
        {data.notifications.length === 0 ? (
          <EmptyState title="No notifications" description="There are no counsellor-scoped notifications for your assigned records." />
        ) : (
          <div className="mt-4 grid gap-3">
            {data.notifications.map((notification) => (
              <div key={notification.id} className="rounded-2xl bg-slate-50 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="text-sm font-extrabold text-slate-900">{notification.title}</p>
                  <span className={`rounded-full px-2 py-1 text-[10px] font-extrabold ${notification.is_read ? "bg-slate-200 text-slate-600" : "bg-saathi-100 text-saathi-800"}`}>
                    {notification.is_read ? "Read" : "Unread"}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600">{notification.message}</p>
                <p className="mt-2 text-[11px] text-slate-500">{new Date(notification.created_at).toLocaleString()}{notification.is_demo ? " · DEMO DATA" : ""}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function AggregateCard({ icon: Icon, label, value }: { icon: typeof Inbox; label: string; value: number }) {
  return (
    <Card>
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-saathi-50 text-saathi-700"><Icon size={19} /></span>
        <div>
          <p className="text-[11px] font-bold text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-extrabold text-slate-900">{value}</p>
        </div>
      </div>
    </Card>
  );
}

function SectionHeading({ title, description }: { title: string; description: string }) {
  return <div><h2 className="text-lg font-extrabold text-slate-900">{title}</h2><p className="mt-1 text-sm leading-6 text-slate-500">{description}</p></div>;
}

function ActionList({ actions }: { actions: CounsellorDashboard["support_actions"] }) {
  return (
    <div className="mt-4 grid gap-3">
      {actions.map((action) => (
        <div key={action.id} className="rounded-2xl border border-slate-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-extrabold text-slate-900">Request #{action.support_request_id} · {action.action}</p>
            <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-extrabold text-slate-600">{action.status}</span>
          </div>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{action.notes}</p>
          <p className="mt-2 text-[11px] text-slate-500">{new Date(action.created_at).toLocaleString()}{action.is_demo ? " · DEMO DATA" : ""}</p>
        </div>
      ))}
    </div>
  );
}

function DemoBadge() {
  return <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[10px] font-extrabold text-amber-800">DEMO DATA</span>;
}
