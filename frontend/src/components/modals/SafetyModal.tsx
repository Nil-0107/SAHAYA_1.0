import { ArrowLeft, ExternalLink, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { immediateHelpResources } from "../../config/immediateHelp";
import { Button } from "../common/Button";
import { Modal } from "./Modal";

export function SafetyModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [view, setView] = useState<"question" | "help">("question");

  useEffect(() => {
    if (open) setView("question");
  }, [open]);

  return (
    <Modal open={open} onClose={onClose} title="Immediate danger check">
      {view === "question" ? (
        <div>
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-red-50 text-red-700"><ShieldAlert size={23} /></span>
          <p className="mt-5 text-[11px] font-extrabold uppercase tracking-[0.16em] text-red-700">Immediate safety check</p>
          <h2 className="mt-2 text-2xl font-extrabold text-slate-900">Are you in immediate danger?</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">General emotional support and check-ins are available below. If you may be in immediate danger, choose Yes to see the configured immediate-help information.</p>
          <div className="mt-6 grid gap-2 sm:grid-cols-2">
            <Button variant="danger" onClick={() => setView("help")}>Yes, show immediate help</Button>
            <Button variant="secondary" onClick={onClose}>No, continue support</Button>
          </div>
          <button type="button" onClick={onClose} className="mt-5 w-full rounded-xl px-3 py-2 text-xs font-extrabold text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-saathi-500">Close and return to SAATHI</button>
        </div>
      ) : (
        <div>
          <button type="button" onClick={() => setView("question")} className="mb-4 inline-flex items-center gap-2 rounded-lg px-2 py-1 text-xs font-extrabold text-saathi-700 focus:outline-none focus:ring-2 focus:ring-saathi-500"><ArrowLeft size={15} /> Back</button>
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-red-50 text-red-700"><ShieldAlert size={23} /></span>
          <h2 className="mt-5 text-[11px] font-extrabold uppercase tracking-[0.16em] text-red-700">Immediate help</h2>
          <p className="mt-2 text-2xl font-extrabold text-slate-900">If you are in immediate danger, use a trusted local emergency resource.</p>
          <p className="mt-3 text-sm leading-6 text-slate-600">SAATHI has not contacted emergency services, authorities, police, counsellors, or any other person. Your location has not been shared.</p>
          {immediateHelpResources.length > 0 ? (
            <div className="mt-5 grid gap-3">
              {immediateHelpResources.map((resource) => (
                <div key={`${resource.label}-${resource.href ?? resource.description ?? "resource"}`} className="rounded-2xl border border-red-200 bg-red-50 p-4">
                  <p className="text-sm font-extrabold text-red-950">{resource.label}</p>
                  {resource.description ? <p className="mt-1 text-xs leading-5 text-red-900">{resource.description}</p> : null}
                  {resource.href ? <a href={resource.href} target={resource.href.startsWith("tel:") ? undefined : "_blank"} rel={resource.href.startsWith("tel:") ? undefined : "noreferrer"} className="mt-3 inline-flex items-center gap-2 text-xs font-extrabold text-red-800 underline focus:outline-none focus:ring-2 focus:ring-red-500">{resource.href.startsWith("tel:") ? "Call configured resource" : "Open configured resource"}<ExternalLink size={14} aria-hidden /></a> : null}
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-900">No emergency resources are configured in this application. No integration has been activated.</div>
          )}
          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="secondary" onClick={() => setView("question")}>Back to question</Button>
            <Button onClick={onClose}>Exit immediate help</Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
