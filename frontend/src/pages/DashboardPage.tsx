import { useEffect, useMemo, useState } from "react";
import { Download, LogOut, MailCheck, MailOpen, RefreshCcw, Users } from "lucide-react";
import LeadDetail from "../components/LeadDetail";
import LeadTable from "../components/LeadTable";
import SearchPanel from "../components/SearchPanel";
import StatCard from "../components/StatCard";
import { api } from "../services/api";
import type { Lead, User } from "../types/api";
import { downloadBlob } from "../utils/download";

type Props = {
  token: string;
  user: User;
  onLogout: () => void;
};

export default function DashboardPage({ token, user, onLogout }: Props) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selected, setSelected] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const stats = useMemo(() => {
    const draft = leads.filter((lead) => lead.email_status === "draft").length;
    const sent = leads.filter((lead) => lead.email_status === "sent").length;
    const replied = leads.filter((lead) => lead.email_status === "replied").length;
    const avg = leads.length
      ? Math.round(leads.reduce((total, lead) => total + lead.quality_score, 0) / leads.length)
      : 0;
    return { draft, sent, replied, avg };
  }, [leads]);

  async function loadLeads() {
    setError(null);
    try {
      const nextLeads = await api.listLeads(token);
      setLeads(nextLeads);
      if (selected) {
        setSelected(nextLeads.find((lead) => lead.id === selected.id) || null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load leads");
    }
  }

  useEffect(() => {
    loadLeads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function runSearch(city: string, niche: string, limit: number) {
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const response = await api.searchLeads(token, city, niche, limit);
      setNotice(response.message);
      await loadLeads();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(leadId: string, status: string) {
    setError(null);
    try {
      const updated = await api.updateLeadStatus(token, leadId, status);
      setLeads((current) => current.map((lead) => (lead.id === leadId ? updated : lead)));
      setSelected(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    }
  }

  async function sendEmail(leadId: string) {
    setSending(true);
    setError(null);
    setNotice(null);
    try {
      const response = await api.sendEmail(token, leadId);
      setNotice(response.message);
      await loadLeads();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sending failed");
    } finally {
      setSending(false);
    }
  }

  async function exportCsv() {
    setError(null);
    try {
      const blob = await api.exportCsv(token);
      downloadBlob(blob, "leadhive-leads.csv");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f4ed] text-ink">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-4">
          <div>
            <p className="text-sm font-semibold text-leaf">LeadHive Automation</p>
            <h1 className="text-2xl font-semibold">Outreach dashboard</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden text-sm text-slate-600 sm:inline">{user.email}</span>
            <button className="focus-ring rounded-md p-2 hover:bg-slate-100" onClick={loadLeads} aria-label="Refresh leads">
              <RefreshCcw className="h-4 w-4" />
            </button>
            <button className="focus-ring rounded-md p-2 hover:bg-slate-100" onClick={exportCsv} aria-label="Export CSV">
              <Download className="h-4 w-4" />
            </button>
            <button className="focus-ring rounded-md p-2 hover:bg-slate-100" onClick={onLogout} aria-label="Log out">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-6 py-6">
        <SearchPanel loading={loading} onSearch={runSearch} />

        {notice ? <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p> : null}
        {error ? <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}

        <section className="grid gap-4 md:grid-cols-4">
          <StatCard label="Total leads" value={leads.length} icon={<Users className="h-5 w-5" />} />
          <StatCard label="Draft emails" value={stats.draft} icon={<MailOpen className="h-5 w-5" />} />
          <StatCard label="Sent emails" value={stats.sent} icon={<MailCheck className="h-5 w-5" />} />
          <StatCard label="Average score" value={stats.avg} icon={<RefreshCcw className="h-5 w-5" />} />
        </section>

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_420px]">
          <LeadTable leads={leads} selectedId={selected?.id} onSelect={setSelected} />
          <LeadDetail
            lead={selected}
            sending={sending}
            onClose={() => setSelected(null)}
            onSend={sendEmail}
            onStatus={updateStatus}
          />
        </section>
      </div>
    </main>
  );
}

