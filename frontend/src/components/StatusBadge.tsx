const styles: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700",
  sent: "bg-blue-50 text-blue-700",
  replied: "bg-emerald-50 text-emerald-700",
  bounced: "bg-red-50 text-red-700",
  opted_out: "bg-zinc-200 text-zinc-700"
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${styles[status] || styles.draft}`}>
      {status.replace("_", " ")}
    </span>
  );
}

