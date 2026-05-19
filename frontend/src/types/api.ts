export type Issue = {
  code: string;
  label: string;
  severity: "low" | "medium" | "high" | string;
  evidence: string;
};

export type Lead = {
  id: string;
  batch_id: string;
  city: string;
  niche: string;
  business_name: string;
  website: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  source_url: string | null;
  quality_score: number;
  issues: Issue[];
  generated_email_subject: string | null;
  generated_email_body: string | null;
  email_status: "draft" | "sent" | "replied" | "bounced" | "opted_out" | string;
  created_at: string;
  updated_at: string;
};

export type User = {
  id: string;
  email: string;
};

export type SearchResponse = {
  batch_id: string;
  created: number;
  message: string;
};

