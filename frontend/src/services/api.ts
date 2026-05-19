import type { Lead, SearchResponse, User } from "../types/api";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type RequestOptions = RequestInit & {
  token?: string | null;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  register: (email: string, password: string) =>
    request<{ access_token: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  me: (token: string) => request<User>("/api/auth/me", { token }),
  searchLeads: (token: string, city: string, niche: string, limit: number) =>
    request<SearchResponse>("/api/jobs/search", {
      method: "POST",
      token,
      body: JSON.stringify({ city, niche, limit })
    }),
  listLeads: (token: string) => request<Lead[]>("/api/leads", { token }),
  updateLeadStatus: (token: string, leadId: string, email_status: string) =>
    request<Lead>(`/api/leads/${leadId}/status`, {
      method: "PATCH",
      token,
      body: JSON.stringify({ email_status })
    }),
  sendEmail: (token: string, leadId: string) =>
    request<{ status: string; message: string }>(`/api/email/send/${leadId}`, {
      method: "POST",
      token
    }),
  exportCsv: async (token: string) => {
    const response = await fetch(`${API_URL}/api/export/leads.csv`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!response.ok) {
      throw new Error("CSV export failed");
    }
    return response.blob();
  }
};

