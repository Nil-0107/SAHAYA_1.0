import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { BrainCircuit, BriefcaseBusiness, ChevronRight, FileText, FileUp, HeartHandshake, LineChart, ListChecks, Mic2, NotebookPen, RefreshCw, Scale, ShieldAlert, ShieldCheck } from "lucide-react";
import { Button } from "../../components/common/Button";
import { Card, CardDescription, CardHeader, CardTitle } from "../../components/common/Card";
import { EmptyState, InlineAlert, LoadingState, NotConfiguredState } from "../../components/feedback/FeedbackStates";
import { FormField, TextArea, TextInput } from "../../components/forms/FormField";
import { authErrorMessage } from "../../utils/authErrors";
import { aiApi, health as aiHealth, transcribeVoice, speakText } from "../../services/aiApi";
import { checkinApi } from "../../services/checkinApi";
import { caseApi } from "../../services/caseApi";
import { supportApi } from "../../services/supportApi";
import type { AIChatMessage } from "../../types/ai";
import type { Case } from "../../types/case";
import type { Checkin } from "../../types/checkin";
import type { SupportCategory, SupportRequest } from "../../types/support";
import { SafetyModal } from "../../components/modals/SafetyModal";

export function VictimDashboardPage() {
  const [safetyOpen, setSafetyOpen] = useState(false);
  const location = useLocation();
  const activeTab = location.hash.replace(/^#/, '') || 'overview';

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [activeTab]);

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'check-in':
        return (
          <DashboardSection eyebrow="Periodic assessment" title="Well-being check" icon={<NotebookPen size={19} />} description="Answer 10 open-ended questions in your own words. Your responses are submitted together as one private check-in and analyzed by the supplied local classification model.">
            <CheckinPanel />
          </DashboardSection>
        );
      case 'ai-support':
        return (
          <DashboardSection eyebrow="Support layer" title="AI support" icon={<BrainCircuit size={19} />} description="A calm, clearly identified AI support conversation. It cannot diagnose, make legal determinations, or contact anyone.">
            <AIChatPanel onImmediateDanger={() => setSafetyOpen(true)} />
          </DashboardSection>
        );
      case 'my-case':
        return (
          <DashboardSection eyebrow="Case journey" title="My case" icon={<BriefcaseBusiness size={19} />} description="Review your case information and upload case documents through the secure document workflow.">
            <CasePanel />
          </DashboardSection>
        );
      case 'my-progress':
        return (
          <DashboardSection eyebrow="Longitudinal view" title="My progress" icon={<LineChart size={19} />} description="Your saved check-ins and model outputs are shown here without turning them into a clinical diagnosis.">
            <ProgressPanel />
          </DashboardSection>
        );
      case 'my-summary':
        return (
          <DashboardSection eyebrow="Plain-language view" title="My summary" icon={<ShieldCheck size={19} />} description="A summary of your own submitted information and support activity.">
            <SummaryPanel />
          </DashboardSection>
        );
      case 'legal-assistance':
        return (
          <DashboardSection eyebrow="Legal information" title="Legal assistance" icon={<Scale size={19} />} description="Legal-support requests are handled through the authorised support workflow.">
            <LegalPanel />
          </DashboardSection>
        );
      case 'support':
        return (
          <DashboardSection eyebrow="Human assistance" title="Support requests" icon={<HeartHandshake size={19} />} description="Request authorised human support for counselling, legal help, or protection/relocation.">
            <SupportPanel />
          </DashboardSection>
        );
      default:
        return <OverviewPanel onCheckin={() => { window.location.hash = 'check-in'; }} onSupport={() => { window.location.hash = 'support'; }} onSafety={() => setSafetyOpen(true)} />;
    }
  };

  return (
    <div className="grid gap-7">
      {renderActiveTab()}
      <SafetyModal open={safetyOpen} onClose={() => setSafetyOpen(false)} />
    </div>
  );
}

function OverviewPanel({ onCheckin, onSupport, onSafety }: { onCheckin: () => void; onSupport: () => void; onSafety: () => void }) {
  const [latest, setLatest] = useState<Checkin | null>(null);
  useEffect(() => { void checkinApi.listMine().then((items) => setLatest(items[0] ?? null)).catch(() => setLatest(null)); }, []);
  return (
    <>
      <section className="grid gap-5 xl:grid-cols-[1.45fr_.75fr]">
        <div className="rounded-[22px] border border-teal-100 bg-[linear-gradient(135deg,#e8f4f2,#fff)] p-6 sm:p-8">
          <p className="text-[11px] font-extrabold uppercase tracking-[.16em] text-saathi-700">Welcome</p>
          <h1 className="mt-3 max-w-2xl text-3xl font-extrabold leading-tight text-slate-900 sm:text-4xl">You don’t have to go through it alone.</h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">Use the left navigation to move between your well-being check, AI support, case, progress, summary, legal assistance and human support. Only the selected section is shown.</p>
          <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:flex-wrap"><Button onClick={onCheckin} icon={<NotebookPen size={16} />}>Start well-being check</Button><Button variant="secondary" onClick={onSupport} icon={<HeartHandshake size={16} />}>Get human support</Button><Button variant="danger" onClick={onSafety} icon={<ShieldAlert size={16} />}>I’m not safe</Button></div>
        </div>
        <Card className="flex flex-col justify-center">
          <p className="text-[11px] font-extrabold uppercase tracking-[.14em] text-saathi-700">Latest local ML result</p>
          <div className="mt-4 rounded-2xl bg-slate-50 p-5"><p className="text-3xl font-black text-slate-900">{latest?.confidence != null ? `${Math.round(latest.confidence * 100)}%` : "—"}</p><p className="mt-1 text-xs font-bold text-slate-600">model confidence</p><p className="mt-3 text-xs text-slate-500">{latest ? `Class ${latest.class_id ?? "—"} · ${latest.model_version ?? "local classifier"}` : "Complete a well-being check to see the result."}</p></div>
          <p className="mt-4 text-xs leading-5 text-slate-500">This is a model output, not a clinical diagnosis or safety score.</p>
        </Card>
      </section>
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><QuickAction icon={<NotebookPen size={18} />} title="Well-being" text="Answer 10 open-ended questions." onClick={onCheckin} /><QuickAction icon={<BriefcaseBusiness size={18} />} title="My case" text="Review your case and upload documents." onClick={() => { window.location.hash = 'my-case'; }} /><QuickAction icon={<BrainCircuit size={18} />} title="AI support" text="Start a supportive conversation." onClick={() => { window.location.hash = 'ai-support'; }} /><QuickAction icon={<HeartHandshake size={18} />} title="Human support" text="Create a support request." onClick={onSupport} /></section>
    </>
  );
}

function QuickAction({ icon, title, text, onClick }: { icon: ReactNode; title: string; text: string; onClick: () => void }) {
  return <button type="button" onClick={onClick} className="rounded-2xl border border-slate-200 bg-white p-5 text-left transition hover:-translate-y-0.5 hover:border-teal-300 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-saathi-500"><span className="grid h-10 w-10 place-items-center rounded-xl bg-saathi-50 text-saathi-700">{icon}</span><h2 className="mt-4 text-sm font-extrabold text-slate-900">{title}</h2><p className="mt-1 text-xs leading-5 text-slate-500">{text}</p></button>;
}

function ProgressPanel() {
  const [checkins, setCheckins] = useState<Checkin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => { void checkinApi.listMine().then(setCheckins).catch((caught) => setError(authErrorMessage(caught, 'Unable to load progress.'))).finally(() => setLoading(false)); }, []);
  if (loading) return <LoadingState label="Loading your progress…" />;
  if (error) return <InlineAlert>{error}</InlineAlert>;
  if (!checkins.length) return <EmptyState title="No progress data yet" description="Complete your first 10-question well-being check to begin building your private history." />;
  const points = [...checkins].reverse().filter((item) => item.confidence != null);
  const max = 1;
  const width = 680; const height = 190; const pad = 24;
  const path = points.length > 1 ? points.map((item, i) => { const x = pad + (i*(width-pad*2))/Math.max(1,points.length-1); const y=height-pad-(item.confidence!/max)*(height-pad*2); return `${i===0?'M':'L'} ${x} ${y}`; }).join(' ') : '';
  return <div className="grid gap-5">
    <div className="rounded-2xl border border-slate-200 bg-white p-4"><div className="flex items-center justify-between gap-3"><div><h3 className="text-base font-extrabold text-slate-900">Model-confidence trend</h3><p className="mt-1 text-xs text-slate-500">Actual confidence returned by the supplied TF-IDF + Logistic Regression pipeline.</p></div><span className="rounded-full bg-saathi-50 px-2 py-1 text-[10px] font-extrabold text-saathi-700">Not a risk score</span></div>{points.length < 2 ? <p className="mt-5 text-xs text-slate-500">Submit at least two analyzed check-ins to see the trend.</p> : <div className="mt-4 overflow-x-auto"><svg viewBox={`0 0 ${width} ${height}`} className="h-48 min-w-[660px] w-full"><line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="currentColor" className="text-slate-300" /><path d={path} fill="none" stroke="currentColor" strokeWidth="3" className="text-saathi-700" />{points.map((item,i)=>{const x=pad+(i*(width-pad*2))/Math.max(1,points.length-1);const y=height-pad-(item.confidence!/max)*(height-pad*2);return <circle key={item.id} cx={x} cy={y} r="4" className="fill-saathi-700"/>;})}</svg></div>}</div>
    <div className="grid gap-3">{checkins.map((item) => <CheckinHistoryItem key={item.id} checkin={item} />)}</div>
  </div>;
}

function SummaryPanel() {
  return <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5"><h3 className="text-sm font-extrabold text-slate-900">Your SAATHI summary</h3><p className="mt-2 text-sm leading-6 text-slate-600">Your summary is built from information you submit through your profile, well-being checks, case and support workflows. No unsupported diagnosis or risk score is generated.</p><div className="mt-4 grid gap-3 sm:grid-cols-3"><div className="rounded-xl bg-white p-3"><p className="text-[10px] font-bold uppercase text-slate-500">Well-being</p><p className="mt-1 text-xs font-bold text-slate-800">See My progress</p></div><div className="rounded-xl bg-white p-3"><p className="text-[10px] font-bold uppercase text-slate-500">Case</p><p className="mt-1 text-xs font-bold text-slate-800">See My case</p></div><div className="rounded-xl bg-white p-3"><p className="text-[10px] font-bold uppercase text-slate-500">Support</p><p className="mt-1 text-xs font-bold text-slate-800">See Support</p></div></div></div>;
}

function LegalPanel() {
  return <div className="grid gap-4 sm:grid-cols-2"><div className="rounded-2xl border border-slate-200 bg-white p-5"><Scale className="text-saathi-700" size={22} /><h3 className="mt-3 text-sm font-extrabold text-slate-900">Legal support request</h3><p className="mt-2 text-xs leading-5 text-slate-500">Use the Support tab to request authorised legal assistance. SAATHI does not provide legal advice as a substitute for a qualified professional.</p><button type="button" onClick={() => { window.location.hash = 'support'; }} className="mt-4 rounded-xl bg-saathi-900 px-4 py-2.5 text-xs font-extrabold text-white">Request legal help</button></div><div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5"><p className="text-sm font-extrabold text-slate-800">External legal integrations</p><p className="mt-2 text-xs leading-5 text-slate-500">No external lawyer, court or IVRS system is contacted automatically.</p></div></div>;
}

function SupportPanel() {
  const [cases, setCases] = useState<Case[]>([]);
  const [requests, setRequests] = useState<SupportRequest[]>([]);
  const [caseId, setCaseId] = useState<number | null>(null);
  const [category, setCategory] = useState<SupportCategory>("counselling");
  const [details, setDetails] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    void Promise.all([caseApi.listMine(), supportApi.listMine()])
      .then(([caseItems, requestItems]) => {
        setCases(caseItems);
        setRequests(requestItems);
        setCaseId((current) => current ?? caseItems[0]?.id ?? null);
      })
      .catch((caught) => setError(authErrorMessage(caught, "Unable to load support requests.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (!caseId || !details.trim()) {
      setError("Choose a case and enter what support you need.");
      return;
    }
    setCreating(true);
    try {
      const created = await supportApi.create({ case_id: caseId, category, details });
      setRequests((current) => [created, ...current]);
      setDetails("");
      setSuccess("Support request saved with pending status. No external person has been contacted yet.");
    } catch (caught) {
      setError(authErrorMessage(caught, "Unable to create the support request."));
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <LoadingState label="Loading support requests…" />;
  return (
    <div className="grid gap-5">
      {error ? <InlineAlert>{error}</InlineAlert> : null}
      <form className="grid gap-4" onSubmit={submit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1.5 text-xs font-extrabold text-slate-700">Case<select value={caseId ?? ""} onChange={(event) => setCaseId(Number(event.target.value))} required className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm font-normal outline-none focus:border-saathi-500 focus:ring-2 focus:ring-teal-100">{cases.length === 0 ? <option value="">No case available</option> : cases.map((item) => <option key={item.id} value={item.id}>{item.case_number}{item.is_demo ? " · DEMO DATA" : ""}</option>)}</select></label>
          <label className="grid gap-1.5 text-xs font-extrabold text-slate-700">Support category<select value={category} onChange={(event) => setCategory(event.target.value as SupportCategory)} className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm font-normal outline-none focus:border-saathi-500 focus:ring-2 focus:ring-teal-100"><option value="counselling">Counselling</option><option value="legal_help">Legal help</option><option value="protection_relocation">Protection / relocation</option></select></label>
        </div>
        <FormField label="What support do you need?" hint="Your request is private. Assignment and status are controlled by authorised staff workflows."><TextArea required maxLength={4000} value={details} onChange={(event) => setDetails(event.target.value)} placeholder="Share the next step you would like help with…" /></FormField>
        {success ? <InlineAlert tone="success">{success}</InlineAlert> : null}
        <div className="flex justify-end"><Button type="submit" loading={creating} disabled={!caseId}>Request support</Button></div>
      </form>
      <div><div className="mb-3 flex items-center justify-between"><div><h3 className="text-base font-extrabold text-slate-900">Your support requests</h3><p className="mt-1 text-xs text-slate-500">Status and updates come from the backend.</p></div><Button variant="ghost" onClick={load} icon={<RefreshCw size={15} />}>Refresh</Button></div>{requests.length === 0 ? <EmptyState title="No support requests" description="Your submitted requests and their authorised updates will appear here." /> : <div className="grid gap-3">{requests.map((request) => <SupportRequestCard key={request.id} request={request} />)}</div>}</div>
    </div>
  );
}

function SupportRequestCard({ request }: { request: SupportRequest }) {
  const categoryLabel: Record<SupportCategory, string> = { counselling: "Counselling", legal_help: "Legal help", protection_relocation: "Protection / relocation" };
  return <article className="rounded-2xl border border-slate-200 bg-white p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-sm font-extrabold text-slate-900">{categoryLabel[request.category]}</p><p className="mt-1 text-[10px] text-slate-500">Request #{request.id} · {new Date(request.created_at).toLocaleString()}</p></div><div className="flex items-center gap-2"><span className="rounded-full bg-saathi-50 px-2.5 py-1 text-[10px] font-extrabold uppercase text-saathi-700">{request.status.replace("_", " ")}</span>{request.is_demo ? <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[10px] font-extrabold text-amber-800">DEMO DATA</span> : null}</div></div><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{request.details}</p>{request.assignments.length > 0 ? <p className="mt-3 text-[11px] font-bold text-slate-500">Assignment status: {request.assignments.map((assignment) => assignment.status).join(", ")}</p> : null}<div className="mt-3 border-t border-slate-100 pt-3"><p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">Updates</p>{request.updates.length === 0 ? <p className="mt-2 text-xs text-slate-500">No updates yet.</p> : <div className="mt-2 grid gap-2">{request.updates.map((update) => <div key={update.id} className="rounded-xl bg-slate-50 p-3 text-xs"><div className="flex justify-between gap-3 font-bold text-slate-700"><span>{update.action.replaceAll("_", " ")}</span><time className="text-[10px] text-slate-500">{new Date(update.created_at).toLocaleString()}</time></div><p className="mt-1 leading-5 text-slate-600">{update.notes}</p></div>)}</div>}</div></article>;
}

function CasePanel() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [upload, setUpload] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [creatingCase, setCreatingCase] = useState(false);
  const [caseCreateError, setCaseCreateError] = useState("");
  const [caseSummary, setCaseSummary] = useState("");

  const loadCases = () => {
    setLoading(true);
    setError("");
    void caseApi.listMine()
      .then((items) => {
        setCases(items);
        setSelectedCaseId((current) => current ?? items[0]?.id ?? null);
      })
      .catch((caught) => setError(authErrorMessage(caught, "Unable to load your case information.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadCases(); }, []);

  useEffect(() => {
    if (selectedCaseId === null) {
      setSelectedCase(null);
      return;
    }
    void caseApi.get(selectedCaseId)
      .then(setSelectedCase)
      .catch((caught) => setError(authErrorMessage(caught, "Unable to load the selected case.")));
  }, [selectedCaseId]);

  const createCase = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setCaseCreateError("");
    setCreatingCase(true);
    try {
      const created = await caseApi.create({ category: "general_support", summary: caseSummary || null });
      setCases((current) => [created, ...current]);
      setSelectedCaseId(created.id);
      setCaseSummary("");
    } catch (caught) {
      setCaseCreateError(authErrorMessage(caught, "Unable to create your case."));
    } finally {
      setCreatingCase(false);
    }
  };

  const submitUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setUploadError("");
    setUploadSuccess("");
    if (!upload) {
      setUploadError("Select a PDF, JPG, JPEG, or PNG file first.");
      return;
    }
    setUploading(true);
    try {
      let targetCase = selectedCase;
      if (!targetCase) {
        targetCase = await caseApi.create({ category: "uploaded_document", summary: "Case created from uploaded document" });
        setCases((current) => [targetCase!, ...current]);
        setSelectedCaseId(targetCase.id);
      }
      await caseApi.uploadDocument(targetCase.id, upload);
      setUpload(null);
      setUploadSuccess("Document uploaded successfully. It is stored securely and routed to your authorised support scope.");
      const refreshed = await caseApi.get(targetCase.id);
      setSelectedCase(refreshed);
    } catch (caught) {
      setUploadError(authErrorMessage(caught, "Unable to upload the document."));
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <LoadingState label="Loading your case information…" />;
  if (error && cases.length === 0) return <InlineAlert>{error}</InlineAlert>;
  if (cases.length === 0) {
    // Continue rendering the upload panel below; uploading without a case automatically creates a private case.
  }

  return (
    <div className="grid gap-5">
      {cases.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-4"><p className="text-sm font-extrabold text-slate-900">No case yet</p><p className="mt-1 text-xs text-slate-500">You can create a private case first, or simply upload a case document below and SAATHI will create the private case automatically.</p><form className="mt-3 grid gap-3" onSubmit={createCase}><FormField label="Optional case context"><TextArea maxLength={4000} value={caseSummary} onChange={(event) => setCaseSummary(event.target.value)} placeholder="Briefly describe what you need help with…" /></FormField><VoiceRecorder label="Speak your case statement" onTranscript={(text) => setCaseSummary((current) => current ? `${current}\n${text}` : text)} />{caseCreateError ? <InlineAlert>{caseCreateError}</InlineAlert> : null}<div className="flex justify-end"><Button type="submit" loading={creatingCase}>Create private case</Button></div></form></div> : null}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="grid gap-1"><p className="text-[10px] font-extrabold uppercase tracking-[.14em] text-saathi-700">Your cases</p><select aria-label="Select a case" value={selectedCaseId ?? ""} onChange={(event) => setSelectedCaseId(Number(event.target.value))} className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm font-bold text-slate-800 outline-none focus:border-saathi-500 focus:ring-2 focus:ring-teal-100">{cases.map((item) => <option key={item.id} value={item.id}>{item.case_number}{item.is_demo ? " · DEMO DATA" : ""}</option>)}</select></div>
        <Button variant="ghost" onClick={loadCases} icon={<RefreshCw size={15} />}>Refresh</Button>
      </div>
      {error ? <InlineAlert>{error}</InlineAlert> : null}
      {selectedCase ? <CaseDetails currentCase={selectedCase} /> : <LoadingState label="Loading selected case…" />}
      <div>
        <h3 className="text-base font-extrabold text-slate-900">Add a case document</h3>
        <p className="mt-1 text-xs leading-5 text-slate-500">Only PDF, JPG, JPEG, and PNG files up to 10 MB are accepted. Files are stored under a generated name and are not verified as government or court documents.</p>
        <form className="mt-4 grid gap-3" onSubmit={submitUpload}>
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-teal-200 bg-teal-50/40 px-5 py-7 text-center transition hover:border-teal-400 focus-within:ring-2 focus-within:ring-saathi-500"><FileUp className="text-saathi-700" size={23} /><span className="mt-2 text-sm font-extrabold text-slate-800">Choose a document to upload</span><span className="mt-1 text-xs text-slate-500">PDF, JPG, JPEG, or PNG · maximum 10 MB</span><input type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" className="sr-only" onChange={(event) => setUpload(event.target.files?.[0] ?? null)} /></label>
          {upload ? <p className="text-xs font-bold text-slate-600">Selected: {upload.name}</p> : null}
          {uploadError ? <InlineAlert>{uploadError}</InlineAlert> : null}
          {uploadSuccess ? <InlineAlert tone="success">{uploadSuccess}</InlineAlert> : null}
          <div className="flex justify-end"><Button type="submit" loading={uploading} disabled={!upload}>Upload securely</Button></div>
        </form>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <CaseEntryPoint icon={<FileText size={18} />} title="e-Courts CNR lookup" description="External CNR integration is not enabled in this local build." />
        <div className="rounded-2xl border border-slate-200 bg-white p-4"><Mic2 className="text-saathi-700" size={18} /><h3 className="mt-3 text-sm font-extrabold text-slate-900">Voice statement</h3><p className="mt-1 text-xs leading-5 text-slate-500">Record a statement and Gemini transcribes it into your case context.</p><div className="mt-3"><VoiceRecorder label="Record voice statement" onTranscript={(text) => setCaseSummary((current) => current ? `${current}\n${text}` : text)} /></div></div>
        <CaseEntryPoint icon={<ListChecks size={18} />} title="Guided questions" description="Use the 10-question well-being check for structured open-ended reflection." />
      </div>
    </div>
  );
}

function CaseDetails({ currentCase }: { currentCase: Case }) {
  return (
    <div className="grid gap-4">
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-[10px] font-extrabold uppercase tracking-[.14em] text-saathi-700">Case at a glance</p>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-2"><div><p className="text-[10px] font-extrabold uppercase tracking-[.14em] text-slate-500">Case ID</p><h3 className="mt-1 text-base font-extrabold text-slate-900">{currentCase.case_number}</h3></div>{currentCase.is_demo ? <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[10px] font-extrabold text-amber-800">DEMO DATA</span> : null}</div>
        <div className="mt-4 grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-3"><div><p className="font-bold text-slate-500">Current stage</p><p className="mt-1 font-extrabold text-slate-800">{currentCase.stage}</p></div><div><p className="font-bold text-slate-500">Category</p><p className="mt-1 font-extrabold text-slate-800">{currentCase.category}</p></div><div><p className="font-bold text-slate-500">Next hearing</p><p className="mt-1 font-extrabold text-slate-800">{currentCase.next_hearing ? new Date(currentCase.next_hearing).toLocaleString() : "Not recorded"}</p></div><div><p className="font-bold text-slate-500">Protection request</p><p className="mt-1 font-extrabold text-slate-800">{currentCase.protection_request_open ? "Open in demo record" : "None recorded"}</p></div><div><p className="font-bold text-slate-500">Verification</p><p className="mt-1 font-extrabold text-slate-800">{currentCase.category_verified ? "Verified" : "Not verified"}</p></div><div><p className="font-bold text-slate-500">Court name</p><p className="mt-1 font-extrabold text-slate-800">{currentCase.court_name ?? "Not recorded"}</p></div></div>
        <div className="mt-4 border-t border-slate-200 pt-3"><h4 className="text-sm font-extrabold text-slate-900">Summary</h4>{currentCase.summary ? <p className="mt-2 text-xs leading-5 text-slate-600">{currentCase.summary}</p> : <p className="mt-2 text-xs text-slate-500">Not available yet.</p>}</div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 p-4"><h4 className="text-sm font-extrabold text-slate-900">Protection and relief information</h4><div className="mt-3 grid gap-3 text-xs"><div><p className="font-bold text-slate-500">Protection</p><p className="mt-1 font-extrabold text-slate-800">{currentCase.protection_request_open ? "Protection request is marked open in the stored case record." : "Not available yet."}</p></div><div><p className="font-bold text-slate-500">Relief / compensation</p><p className="mt-1 font-extrabold text-slate-800">Not available yet.</p></div></div></div>
        <div className="rounded-2xl border border-slate-200 p-4"><h4 className="text-sm font-extrabold text-slate-900">Documents metadata</h4>{currentCase.documents.length === 0 ? <p className="mt-3 text-xs text-slate-500">Not available yet.</p> : <div className="mt-3 grid gap-2">{currentCase.documents.map((document) => <div key={document.id} className="rounded-xl bg-slate-50 p-3"><p className="text-xs font-extrabold text-slate-800">{document.filename}</p><p className="mt-1 text-[10px] text-slate-500">{document.mime_type} · {document.size_bytes ? `${Math.ceil(document.size_bytes / 1024)} KB` : "Size unavailable"} · {document.status}</p></div>)}</div>}</div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 p-4"><h4 className="text-sm font-extrabold text-slate-900">Support information</h4>{currentCase.support_information.length === 0 ? <p className="mt-3 text-xs text-slate-500">Not available yet.</p> : <div className="mt-3 grid gap-2">{currentCase.support_information.map((support) => <div key={support.id} className="flex items-center justify-between rounded-xl bg-slate-50 p-3 text-xs"><span className="font-extrabold text-slate-800">{support.type} support</span><span className="text-slate-500">{support.status} · {support.priority}</span></div>)}</div>}</div>
        <div className="rounded-2xl border border-slate-200 p-4"><h4 className="text-sm font-extrabold text-slate-900">Updates</h4>{currentCase.updates.length === 0 ? <p className="mt-3 text-xs text-slate-500">Not available yet.</p> : <div className="mt-3 grid gap-2">{currentCase.updates.map((update) => <div key={`${update.date}-${update.label}`} className="rounded-xl bg-slate-50 p-3 text-xs"><time className="font-bold text-slate-500">{update.date}</time><p className="mt-1 text-slate-700">{update.label}</p></div>)}</div>}</div>
      </div>
      <div className="rounded-2xl border border-slate-200 p-4"><h4 className="text-sm font-extrabold text-slate-900">Case timeline</h4>{currentCase.timeline.length === 0 ? <p className="mt-3 text-xs text-slate-500">Not available yet.</p> : <ol className="mt-3 grid gap-3">{currentCase.timeline.map((event) => <li key={`${event.date}-${event.label}`} className="flex gap-3 text-xs"><time className="w-24 shrink-0 font-bold text-slate-500">{event.date}</time><span className="text-slate-700">{event.label}</span></li>)}</ol>}</div>
    </div>
  );
}

function CaseEntryPoint({ icon, title, description }: { icon: ReactNode; title: string; description: string }) {
  return <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4"><span className="grid h-9 w-9 place-items-center rounded-xl bg-white text-slate-500 shadow-sm">{icon}</span><p className="mt-3 text-sm font-extrabold text-slate-800">{title}</p><p className="mt-1 text-xs text-slate-500">{description}</p></div>;
}

function VoiceRecorder({ onTranscript, label = "Voice response" }: { onTranscript: (text: string) => void; label?: string }) {
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<any>(null);

  const start = async () => {
    setError("");
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.lang = "en-IN";
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.onresult = (event: any) => {
          const text = event.results?.[0]?.[0]?.transcript?.trim();
          if (text) onTranscript(text);
        };
        recognition.onerror = () => setError("Browser speech recognition failed. Try recording again or use a Chrome-based browser.");
        recognition.onend = () => setRecording(false);
        recognitionRef.current = recognition;
        recognition.start();
        setRecording(true);
        return;
      } catch {
        // Fall through to recorded-audio transcription.
      }
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("Voice input is not supported by this browser. Use Chrome or Edge for speech-to-text.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      streamRef.current = stream; chunksRef.current = []; recorderRef.current = recorder;
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setBusy(true);
        try { const result = await transcribeVoice(blob); onTranscript(result.transcript); }
        catch (caught) { setError(authErrorMessage(caught, "Voice transcription is unavailable. Add Gemini to the backend or use Chrome speech recognition.")); }
        finally { setBusy(false); }
      };
      recorder.start(); setRecording(true);
    } catch { setError("Microphone access was denied or unavailable."); }
  };
  const stop = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch { /* already stopped */ }
      recognitionRef.current = null;
    }
    if (recorderRef.current && recorderRef.current.state !== "inactive") recorderRef.current.stop();
    setRecording(false);
  };
  return <div className="grid gap-2">
    <Button type="button" variant={recording ? "danger" : "secondary"} loading={busy} onClick={recording ? stop : start} icon={<Mic2 size={16} />}>{busy ? "Transcribing…" : recording ? "Stop recording" : label}</Button>
    {error ? <InlineAlert>{error}</InlineAlert> : null}
  </div>;
}

function AIChatPanel({ onImmediateDanger }: { onImmediateDanger: () => void }) {
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [messages, setMessages] = useState<AIChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [aiConfigured, setAiConfigured] = useState<boolean | null>(null);
  const [aiModel, setAiModel] = useState("");

  useEffect(() => { void aiHealth().then((status) => { setAiConfigured(status.configured); setAiModel(status.model); }).catch(() => setAiConfigured(false)); }, []);

  const sendMessage = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    if (!message.trim()) {
      setError("Enter a message before sending.");
      return;
    }
    setSending(true);
    try {
      const response = await aiApi.chat({ message, conversation_id: conversationId });
      setConversationId(response.conversation_id);
      setMessages((current) => [...current, response.user_message, response.assistant_message]);
      if (response.immediate_danger) onImmediateDanger();
      setMessage("");
    } catch (caught) {
      setError(authErrorMessage(caught, "AI support is temporarily unavailable."));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="grid gap-4">
      <div className={`rounded-xl border p-3 text-xs ${aiConfigured === false ? "border-amber-200 bg-amber-50 text-amber-900" : "border-teal-100 bg-teal-50 text-teal-900"}`}>{aiConfigured === false ? <><strong>Gemini is not configured.</strong> Add <code>GEMINI_API_KEY=...</code> to <code>backend/.env</code> and restart FastAPI.</> : aiConfigured === true ? <><strong>Gemini connected.</strong> Model: {aiModel}</> : "Checking Gemini configuration…"}</div>
      <div className="max-h-80 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50 p-4" aria-live="polite">
        {messages.length === 0 ? <EmptyState title="Start a supportive conversation" description="Messages are sent to the server-side AI support service. No response is generated until you send a message." /> : <div className="grid gap-3">{messages.map((item) => <div key={item.id} className={`rounded-2xl px-4 py-3 ${item.role === "user" ? "ml-auto max-w-[85%] bg-saathi-700 text-white" : "mr-auto max-w-[90%] border border-slate-200 bg-white text-slate-700"}`}><div className="flex items-center justify-between gap-3 text-[10px] font-extrabold uppercase tracking-wider opacity-70"><span>{item.role === "user" ? "You" : item.status === "failed" ? "AI support · fallback" : "AI support"}</span><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleTimeString()}</time></div><p className="mt-2 whitespace-pre-wrap text-sm leading-6">{item.content}</p>{item.role === "assistant" ? <button type="button" className="mt-2 text-[10px] font-extrabold text-saathi-700" onClick={() => void speakText(item.content)}>🔊 Read aloud</button> : null}</div>)}</div>}
      </div>
      <form className="grid gap-3" onSubmit={sendMessage}>
        <FormField label="Message AI support" hint="Do not include information you want to keep private from this conversation.">
          <TextInput required maxLength={4000} value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Ask about a SAATHI workflow or share what you need support with…" />
        </FormField>
        {error ? <InlineAlert>{error}</InlineAlert> : null}
        <div className="grid gap-2 sm:grid-cols-2"><VoiceRecorder label="Speak instead" onTranscript={(text) => setMessage((current) => current ? `${current} ${text}` : text)} /><div className="flex justify-end"><Button type="submit" loading={sending}>Send message</Button></div></div>
      </form>
      <p className="text-[11px] leading-5 text-slate-500">AI support is informational and supportive only. It is not a diagnosis or professional assessment, cannot determine legal outcomes, and cannot contact authorities, emergency services, counsellors, or lawyers.</p>
    </div>
  );
}

function CheckinPanel() {
  const questions = [
    "How have you been feeling emotionally since your last check-in?",
    "What has been the most difficult thing for you recently?",
    "What thoughts or worries have been occupying your mind?",
    "How are things going at home, college/work, or in your daily environment?",
    "Is there anything that has made you feel unsafe, pressured, threatened, or uncomfortable?",
    "What has helped you cope when things have felt difficult?",
    "Who, if anyone, have you been able to talk to about what you are experiencing?",
    "How have your sleep, energy, concentration, or routine been affected?",
    "What kind of support would be most useful to you right now?",
    "Is there anything else you want SAATHI to know about how you are doing?",
  ];
  const [answers, setAnswers] = useState<string[]>(() => Array(10).fill(''));
  const [checkins, setCheckins] = useState<Checkin[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [success, setSuccess] = useState("");

  const loadHistory = () => {
    setLoadingHistory(true);
    setHistoryError("");
    void checkinApi.listMine().then(setCheckins).catch((caught) => setHistoryError(authErrorMessage(caught, "Unable to load check-in history."))).finally(() => setLoadingHistory(false));
  };
  useEffect(() => { loadHistory(); }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitError("");
    setSuccess("");
    const missing = answers.findIndex((answer) => !answer.trim());
    if (missing !== -1) {
      setSubmitError(`Please answer question ${missing + 1}. All 10 questions are required.`);
      return;
    }
    const combinedText = answers.map((answer, index) => `Question ${index + 1}: ${questions[index]}\nAnswer: ${answer.trim()}`).join("\n\n");
    setSubmitting(true);
    try {
      const created = await checkinApi.create({ text: combinedText });
      setCheckins((current) => [created, ...current]);
      setAnswers(Array(10).fill(''));
      setSuccess("Your 10-question well-being check was saved and analyzed.");
    } catch (caught) {
      setSubmitError(authErrorMessage(caught, "Unable to save the well-being check."));
    } finally { setSubmitting(false); }
  };

  return <div className="grid gap-6">
    <div className="rounded-2xl border border-teal-100 bg-teal-50/60 p-5"><p className="text-sm font-extrabold text-saathi-900">10 open-ended questions</p><p className="mt-2 text-xs leading-5 text-slate-600">Answer honestly in your own words. These questions are a well-being reflection, not a clinical diagnosis. Your ten answers are submitted together as one private check-in.</p></div>
    <form className="grid gap-5" onSubmit={submit}>
      {questions.map((question, index) => <div key={question} className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5"><label className="grid gap-2"><span className="text-sm font-extrabold text-slate-900"><span className="mr-2 text-saathi-700">{index + 1}.</span>{question}</span><textarea required rows={5} maxLength={1500} value={answers[index]} onChange={(event) => setAnswers((current) => current.map((answer, i) => i === index ? event.target.value : answer))} placeholder="Write your answer here…" className="w-full resize-y rounded-xl border border-slate-300 bg-white px-3 py-3 text-sm leading-6 text-slate-800 outline-none transition focus:border-saathi-500 focus:ring-2 focus:ring-teal-100" /><VoiceRecorder label="Answer by voice" onTranscript={(text) => setAnswers((current) => current.map((answer, i) => i === index ? `${answer ? `${answer} ` : ""}${text}` : answer))} /></label></div>)}
      {submitError ? <InlineAlert>{submitError}</InlineAlert> : null}
      {success ? <InlineAlert tone="success">{success}</InlineAlert> : null}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><p className="text-[11px] leading-5 text-slate-500">Your answers stay tied to your authenticated account and are processed by the configured local ML model.</p><Button type="submit" loading={submitting}>Submit well-being check</Button></div>
    </form>
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="flex items-start gap-3"><ShieldCheck className="mt-0.5 shrink-0 text-saathi-700" size={18} /><p className="text-[11px] leading-5 text-slate-600">The model returns a classification and optional confidence. SAATHI does not interpret that output as a diagnosis, danger score, or legal determination.</p></div></div>
    <div><div className="mb-3 flex items-center justify-between gap-3"><div><h3 className="text-base font-extrabold text-slate-900">Your check-in history</h3><p className="mt-1 text-xs text-slate-500">Only your authenticated account records are shown.</p></div><Button variant="ghost" onClick={loadHistory} icon={<RefreshCw size={15} />}>Refresh</Button></div>{loadingHistory ? <LoadingState label="Loading your check-in history…" /> : null}{!loadingHistory && historyError ? <InlineAlert>{historyError}</InlineAlert> : null}{!loadingHistory && !historyError && checkins.length === 0 ? <EmptyState title="No check-ins yet" description="Your submitted 10-question reflections will appear here." /> : null}{!loadingHistory && !historyError && checkins.length > 0 ? <div className="grid gap-3">{checkins.map((checkin) => <CheckinHistoryItem key={checkin.id} checkin={checkin} />)}</div> : null}</div>
  </div>;
}

function CheckinHistoryItem({ checkin }: { checkin: Checkin }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <time className="text-[11px] font-bold text-slate-500" dateTime={checkin.created_at}>{new Date(checkin.created_at).toLocaleString()}</time>
        <span className="rounded-full bg-saathi-50 px-2.5 py-1 text-[10px] font-extrabold text-saathi-700">Private check-in</span>
      </div>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{checkin.text}</p>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-slate-100 pt-3 text-[11px] text-slate-500">
        {checkin.class_id !== null ? <span>ML class ID: <strong className="text-slate-700">{checkin.class_id}</strong></span> : <span>ML result not available for this record</span>}
        {checkin.confidence !== null ? <span>Model confidence: <strong className="text-slate-700">{checkin.confidence.toFixed(2)}</strong></span> : null}
        {checkin.label ? <span>Label: <strong className="text-slate-700">{checkin.label}</strong></span> : null}
      </div>
    </article>
  );
}

function DashboardSection({ id, eyebrow, title, description, icon, children }: { id?: string; eyebrow: string; title: string; description: string; icon: ReactNode; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24">
      <Card>
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-saathi-50 text-saathi-700">{icon}</span>
          <div><p className="text-[10px] font-extrabold uppercase tracking-[.14em] text-saathi-700">{eyebrow}</p><h2 className="mt-1 text-xl font-extrabold text-slate-900">{title}</h2><p className="mt-1 text-sm leading-6 text-slate-500">{description}</p></div>
          <ChevronRight className="ml-auto hidden text-slate-300 sm:block" size={20} />
        </div>
        <div className="mt-5">{children}</div>
      </Card>
    </section>
  );
}
