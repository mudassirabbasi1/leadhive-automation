import { Send, X } from "lucide-react";
import type { Lead } from "../types/api";
import StatusBadge from "./StatusBadge";

type Props = {
  lead: Lead | null;
  sending: boolean;
  onClose: () => void;
  onSend: (leadId: string) => Promise<void>;
  onStatus: (leadId: string, status: string) => Promise<void>;
};

const statuses = ["draft", "sent", "replied", "bounced", "opted_out"];

export default function LeadDetail({ lead, sending, onClose, onSend, onStatus }: Props) {
  if (!lead) {
    return (
      <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-slate-600">Select a lead to review the website issues and outreach draft.</p>
      </aside>
    );
  }

  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-ink">{lead.business_name}</h2>
          <p className="text-sm text-slate-600">{lead.address || lead.website || "Public business record"}</p>
        </div>
        <button className="focus-ring rounded-md p-2 hover:bg-slate-100" onClick={onClose} aria-label="Close details">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mb-5 flex items-center gap-3">
        <div className="rounded-md bg-[#fff7e0] px-3 py-2 text-lg font-semibold text-ink">
          {Math.round(lead.quality_score)}/100
        </div>
        <StatusBadge status={lead.email_status} />
        <select
          className="focus-ring rounded-md border border-slate-300 px-2 py-2 text-sm"
          value={lead.email_status}
          onChange={(event) => onStatus(lead.id, event.target.value)}
        >
          {statuses.map((status) => (
            <option key={status} value={status}>
              {status.replace("_", " ")}
            </option>
          ))}
        </select>
      </div>

      <section className="mb-5">
        <h3 className="mb-2 text-sm font-semibold uppercase text-slate-500">Detected issues</h3>
        <div className="space-y-2">
          {lead.issues.map((issue) => (
            <div key={issue.code} className="rounded-md border border-slate-200 p-3">
              <p className="font-medium text-ink">{issue.label}</p>
              <p className="mt-1 text-sm text-slate-600">{issue.evidence}</p>
            </div>
          ))}
          {lead.issues.length === 0 ? <p className="text-sm text-slate-600">No major issues detected.</p> : null}
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-sm font-semibold uppercase text-slate-500">Outreach draft</h3>
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
          <p className="mb-2 font-semibold text-ink">{lead.generated_email_subject}</p>
          <pre className="whitespace-pre-wrap font-sans text-sm leading-6 text-slate-700">
            {lead.generated_email_body}
          </pre>
        </div>
        <button
          className="focus-ring mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-ink px-4 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
          disabled={sending || !lead.email}
          onClick={() => onSend(lead.id)}
        >
          <Send className="h-4 w-4" />
          {sending ? "Sending..." : lead.email ? "Send reviewed email" : "No public email"}
        </button>
      </section>
    </aside>
  );
}

