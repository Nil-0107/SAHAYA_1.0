import { useEffect, useState, type FormEvent } from "react";
import { CheckCircle2, Power, UserPlus } from "lucide-react";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { FormField, TextInput } from "../../components/forms/FormField";
import { EmptyState, InlineAlert, LoadingState } from "../../components/feedback/FeedbackStates";
import { useAuth } from "../../context/AuthContext";
import { adminApi } from "../../services/adminApi";
import type { AdministrativeAccount } from "../../types/administration";
import { authErrorMessage } from "../../utils/authErrors";

export function AdminOperationsPage() {
  const { user } = useAuth();
  const national = user?.role === "national_admin";
  const state = user?.role === "state_admin";
  const district = user?.role === "district_admin";
  const [accounts, setAccounts] = useState<AdministrativeAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const [assignmentRequestId, setAssignmentRequestId] = useState("");
  const [assignmentAssigneeId, setAssignmentAssigneeId] = useState("");
  const [assignmentReason, setAssignmentReason] = useState("");
  const [assignmentSaving, setAssignmentSaving] = useState(false);
  const [form, setForm] = useState({ full_name: "", display_name: "", email: "", phone: "", password: "", state_name: "", district_name: "" });

  const load = () => {
    setLoading(true);
    setError("");
    const request = national ? adminApi.listStateAdministrators() : state ? adminApi.listDistrictAdministrators() : adminApi.listCounsellors();
    void request.then(setAccounts).catch((caught) => setError(authErrorMessage(caught, "Unable to load managed accounts."))).finally(() => setLoading(false));
  };

  useEffect(load, [national, state]);

  const update = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const payload = { full_name: form.full_name, display_name: form.display_name || form.full_name, email: form.email, phone: form.phone, password: form.password, ...(state && user?.state_id ? { state_id: user.state_id } : {}), ...(district && user?.district_id ? { district_id: user.district_id } : {}), ...(national ? { state_name: form.state_name } : {}), ...(state ? { district_name: form.district_name } : {}) };
      const created = national ? await adminApi.createStateAdministrator(payload) : state ? await adminApi.createDistrictAdministrator(payload) : await adminApi.createCounsellor(payload);
      setAccounts((current) => [created, ...current]);
      setForm({ full_name: "", display_name: "", email: "", phone: "", password: "", state_name: "", district_name: "" });
      setSuccess("Account created and notification recorded.");
    } catch (caught) {
      setError(authErrorMessage(caught, "Unable to create the account."));
    } finally {
      setSaving(false);
    }
  };

  const submitAssignment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!assignmentRequestId || !assignmentAssigneeId || !assignmentReason.trim()) {
      setError("Enter a support request ID, select a counsellor, and provide an assignment reason.");
      return;
    }
    setAssignmentSaving(true);
    setError("");
    try {
      await adminApi.createAssignment({ support_request_id: Number(assignmentRequestId), assignee_user_id: Number(assignmentAssigneeId), assignment_type: "wellbeing_counsellor", reason: assignmentReason });
      setAssignmentRequestId("");
      setAssignmentAssigneeId("");
      setAssignmentReason("");
      setSuccess("Assignment created and the counsellor was notified.");
    } catch (caught) {
      setError(authErrorMessage(caught, "Unable to create the assignment."));
    } finally {
      setAssignmentSaving(false);
    }
  };

  const toggleStatus = async (account: AdministrativeAccount) => {
    setError("");
    try {
      const updated = await adminApi.setAccountStatus(account.id, account.status === "active" ? "suspended" : "active");
      setAccounts((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (caught) {
      setError(authErrorMessage(caught, "Unable to update account status."));
    }
  };

  if (loading) return <LoadingState label="Loading managed accounts…" />;
  return <div className="grid gap-6"><Card><div className="flex items-start gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-saathi-50 text-saathi-700"><UserPlus size={19} /></span><div><h1 className="text-lg font-extrabold text-slate-900">{national ? "Register State Administrator" : state ? "Register District Administrator" : "Appoint Counsellor"}</h1><p className="mt-1 text-sm text-slate-500">The backend verifies your role and geographic scope before saving this account.</p></div></div><form className="mt-5 grid gap-4" onSubmit={submit}><div className="grid gap-4 sm:grid-cols-2"><FormField label="Full name"><TextInput required value={form.full_name} onChange={(event) => update("full_name", event.target.value)} /></FormField><FormField label="Display name"><TextInput required value={form.display_name} onChange={(event) => update("display_name", event.target.value)} /></FormField><FormField label="Email"><TextInput required type="email" value={form.email} onChange={(event) => update("email", event.target.value)} /></FormField><FormField label="Mobile"><TextInput required value={form.phone} onChange={(event) => update("phone", event.target.value)} placeholder="+91…" /></FormField><FormField label="Temporary password"><TextInput required type="password" value={form.password} onChange={(event) => update("password", event.target.value)} /></FormField>{national ? <FormField label="State name"><TextInput required value={form.state_name} onChange={(event) => update("state_name", event.target.value)} /></FormField> : null}{state ? <FormField label="District name"><TextInput required value={form.district_name} onChange={(event) => update("district_name", event.target.value)} /></FormField> : null}</div>{error ? <InlineAlert>{error}</InlineAlert> : null}{success ? <InlineAlert tone="success">{success}</InlineAlert> : null}<div className="flex justify-end"><Button type="submit" loading={saving}>Save account</Button></div></form></Card>{district ? <Card><div><h2 className="text-lg font-extrabold text-slate-900">Create counsellor assignment</h2><p className="mt-1 text-sm text-slate-500">Assign an existing support request to an appointed counsellor in your district.</p></div><form className="mt-4 grid gap-4" onSubmit={submitAssignment}><div className="grid gap-4 sm:grid-cols-2"><FormField label="Support request ID"><TextInput required type="number" min={1} value={assignmentRequestId} onChange={(event) => setAssignmentRequestId(event.target.value)} /></FormField><FormField label="Counsellor"><select required value={assignmentAssigneeId} onChange={(event) => setAssignmentAssigneeId(event.target.value)} className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm"><option value="">Select counsellor</option>{accounts.map((account) => <option key={account.id} value={account.id}>{account.display_name}</option>)}</select></FormField></div><FormField label="Assignment reason"><TextInput required value={assignmentReason} onChange={(event) => setAssignmentReason(event.target.value)} /></FormField>{error ? <InlineAlert>{error}</InlineAlert> : null}<div className="flex justify-end"><Button type="submit" loading={assignmentSaving}>Create assignment</Button></div></form></Card> : null}<Card><div className="flex items-center justify-between gap-3"><div><h2 className="text-lg font-extrabold text-slate-900">Managed accounts</h2><p className="mt-1 text-sm text-slate-500">Only accounts inside your authorised scope are returned.</p></div><Button variant="ghost" onClick={load}>Refresh</Button></div>{accounts.length === 0 ? <div className="mt-4"><EmptyState title="No managed accounts" description="Accounts created through the hierarchy appear here." /></div> : <div className="mt-4 grid gap-3">{accounts.map((account) => <div key={account.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 p-4"><div><p className="text-sm font-extrabold text-slate-900">{account.display_name} {account.is_demo ? <span className="ml-2 rounded-full bg-amber-100 px-2 py-1 text-[10px] font-extrabold text-amber-800">DEMO DATA</span> : null}</p><p className="mt-1 text-xs text-slate-500">{account.email} · {account.district_name ?? account.state_name ?? "National scope"}</p><p className="mt-1 text-[10px] text-slate-500">Created {new Date(account.created_at).toLocaleString()}</p></div><Button variant={account.status === "active" ? "secondary" : "primary"} onClick={() => void toggleStatus(account)} icon={account.status === "active" ? <Power size={15} /> : <CheckCircle2 size={15} />}>{account.status === "active" ? "Suspend" : "Reactivate"}</Button></div>)}</div>}</Card></div>;
}
