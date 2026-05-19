import { ExternalLink, Mail, Phone } from "lucide-react";
import type { Lead } from "../types/api";
import StatusBadge from "./StatusBadge";

type Props = {
  leads: Lead[];
  selectedId?: string;
  onSelect: (lead: Lead) => void;
};

export default function LeadTable({ leads, selectedId, onSelect }: Props) {
  if (leads.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center text-slate-600">
        No leads yet. Run a city and niche search to create draft outreach opportunities.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Business</th>
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">Contact</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Issues</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {leads.map((lead) => (
              <tr
                key={lead.id}
                onClick={() => onSelect(lead)}
                className={`cursor-pointer transition hover:bg-[#f4faf7] ${
                  selectedId === lead.id ? "bg-[#eef8f4]" : ""
                }`}
              >
                <td className="px-4 py-3">
                  <p className="font-semibold text-ink">{lead.business_name}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span>{lead.city}</span>
                    {lead.website ? (
                      <a
                        className="inline-flex items-center gap-1 text-leaf hover:underline"
                        href={lead.website}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(event) => event.stopPropagation()}
                      >
                        Website <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : null}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-20 rounded-full bg-slate-200">
                      <div
                        className="h-2 rounded-full bg-honey"
                        style={{ width: `${Math.max(4, Math.min(100, lead.quality_score))}%` }}
                      />
                    </div>
                    <span className="font-semibold">{Math.round(lead.quality_score)}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-600">
                  <div className="flex flex-col gap-1">
                    {lead.email ? (
                      <span className="inline-flex items-center gap-1">
                        <Mail className="h-3 w-3" /> {lead.email}
                      </span>
                    ) : null}
                    {lead.phone ? (
                      <span className="inline-flex items-center gap-1">
                        <Phone className="h-3 w-3" /> {lead.phone}
                      </span>
                    ) : null}
                    {!lead.email && !lead.phone ? <span>No public contact</span> : null}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={lead.email_status} />
                </td>
                <td className="max-w-xs px-4 py-3 text-slate-600">
                  {lead.issues.slice(0, 2).map((issue) => issue.label).join(", ") || "No major issues"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

