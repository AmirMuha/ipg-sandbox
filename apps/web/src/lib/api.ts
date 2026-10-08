/**
 * Typed control-API client (T043) — specs/001-mvp/contracts/control-api.md.
 * Pure control API client; no direct database access (FR-010).
 */

// Two bases, because this module runs in both places. Server components fetch during
// `next start`, inside the container, where `localhost:8080` is the dashboard itself and every
// request failed with "fetch failed" (the scenario controls then never rendered, because the
// page guards them behind `project && ...`). The browser needs the host-reachable
// NEXT_PUBLIC_* value; the server needs the compose-internal ENGINE_URL.
const SERVER_API_BASE =
  process.env.ENGINE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";
const CLIENT_API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

const API_BASE = typeof window === "undefined" ? SERVER_API_BASE : CLIENT_API_BASE;

/**
 * The gateway base a merchant's client should POST to. Exported so the adapter cards can
 * render a real endpoint snippet instead of a path prefix.
 */
export const apiBase = CLIENT_API_BASE;

export type ScenarioOutcome =
  | "approve"
  | "decline"
  | "timeout"
  | "refund"
  | "pending_settle"
  | "verify_fail";

export type TransactionStatus =
  | "initiated"
  | "pending"
  | "settled"
  | "approved"
  | "refunded"
  | "expired"
  | "declined"
  | "failed";

export type DeliveryResult = "delivered" | "failed" | "pending";

export interface Transaction {
  id: string;
  project_id: string;
  adapter_id: string;
  amount_rial: number;
  currency: string;
  status: TransactionStatus;
  forced_scenario: ScenarioOutcome | null;
  effective_scenario: ScenarioOutcome;
  authority: string;
  app_reference?: string;
  description?: string;
  callback_url?: string;
  return_url?: string;
  due_at?: string;
  created_at: string;
  updated_at: string;
  /** Absolute URL of the gateway's hosted checkout page for this transaction. */
  checkout_url?: string | null;
  raw_request?: Record<string, unknown>;
  raw_response?: Record<string, unknown>;
}

export interface Project {
  id: string;
  name: string;
  kind: "local" | "demo";
  tier?: "developer" | "team" | "unlimited";
  daily_requests_cap?: number;
  max_active_adapters?: number;
  default_scenario: ScenarioOutcome;
  history_cap: number;
  webhook_retry_max: number;
  webhook_retry_backoff_s: number[];
  pending_settle_delay_s: number;
  timeout_delay_s: number;
  webhook_url?: string | null;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  auth_provider: string;
  is_admin?: boolean;
}

export interface Subscription {
  tier: string;
  status: string;
  amount_toman: number;
  started_at: string | null;
  expires_at: string | null;
  entitlements: {
    daily_requests_limit: string | number;
    active_adapters_limit: string | number;
    history_retention_days: number;
  };
}

export interface AdminSubscription {
  subscription_id: string;
  project_id: string;
  project_name: string | null;
  buyer_email: string | null;
  tier: string;
  status: string;
  amount_toman: number;
  started_at: string | null;
  expires_at: string | null;
}

export interface QuotaMeters {
  tier: string;
  requests_total: number;
  requests_today: number;
  daily_requests_cap: number;
  requests_remaining_today: number | null;
  active_adapters_count: number;
  max_active_adapters: number;
  transactions_total: number;
  history_retained: number;
  history_cap: number;
  webhook_attempts: number;
  window_resets_at: string;
}

// T075: FR-008 asks for per-adapter configuration *and status*. The engine derives this from
// real transaction/delivery activity rather than a stored field, so it cannot drift.
export type AdapterState = "healthy" | "degraded" | "idle" | "disabled";

export interface AdapterStatus {
  state: AdapterState;
  transactions_total: number;
  transactions_settled: number;
  failed_deliveries: number;
  last_activity_at: string | null;
}

export type Provider =
  | "zarinpal"
  | "idpay"
  | "behpardakht"
  | "saman"
  | "sadad"
  | "parsian"
  | "pasargad"
  | "asan_pardakht"
  | "pardakht_novin"
  | "irankish"
  | "fanava"
  | "sarmayeh"
  | "sizpay";

export interface AdapterConfig {
  id: string;
  project_id: string;
  provider: Provider;
  enabled: boolean;
  api_unit: "rial" | "toman";
  endpoint_path_prefix: string;
  credentials?: Record<string, unknown>;
  status?: AdapterStatus;
  withdrawn_by_operator?: boolean;
}

export interface WebhookDelivery {
  id: string;
  transaction_id: string;
  target_url: string;
  stage: string;
  payload: Record<string, unknown>;
  attempt: number;
  result: DeliveryResult;
  response_status?: number | null;
  error?: string | null;
  created_at: string;
}

export interface Paginated<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

/** POST /transactions/simulate request (control-api.md §2). */
export interface PaymentSimulationRequest {
  adapter: string;
  amount_rial: number;
  forced_scenario?: ScenarioOutcome | null;
  callback_url?: string | null;
  description?: string;
  app_reference?: string;
  /** Walk checkout + verify in one call instead of returning a hosted checkout URL. */
  auto_complete?: boolean;
}

export interface PaymentSimulationResponse {
  transaction: Transaction;
  checkout_url: string | null;
  execution_mode: "interactive" | "auto_completed";
  callback_dispatched: boolean;
}

/** GET /analytics/overview (control-api.md §1) — aggregates over *all* retained rows. */
export interface ProjectAnalyticsOverview {
  total_volume_rial: number;
  total_transactions: number;
  success_rate_percent: number;
  status_breakdown: Record<TransactionStatus, number>;
  scenario_distribution: Record<ScenarioOutcome, number>;
  funnel: {
    initiated: number;
    hosted: number;
    callback: number;
    settled: number;
  };
  webhooks: {
    total_deliveries: number;
    delivered: number;
    failed: number;
    pending: number;
  };
  gateways: {
    configured_total: number;
    active_total: number;
  };
}

/** POST /project/webhook-ping (control-api.md §3). */
export interface WebhookPingResponse {
  ok: boolean;
  target_url: string;
  status_code: number | null;
  latency_ms: number;
  error: string | null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}/api/v1${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (typeof window === "undefined") {
    try {
      const { cookies } = await import("next/headers");
      const cookieStore = cookies();
      const session = cookieStore.get("ipg_session");
      if (session && !headers["Cookie"]) {
        headers["Cookie"] = `ipg_session=${session.value}`;
      }
    } catch {
      // not in a server component context
    }
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
    cache: "no-store",
  });

  if (!res.ok) {
    let errorData: { code?: string; message?: string; details?: Record<string, unknown> } = {};
    try {
      errorData = await res.json();
    } catch {
      // ignore JSON parse error
    }
    throw new ApiError(
      res.status,
      errorData.code || "unknown_error",
      errorData.message || `Request failed with status ${res.status}`,
      errorData.details
    );
  }

  // 204 No Content has no body; res.json() would throw on the empty stream.
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

export async function listTransactions(params?: {
  q?: string;
  page?: number;
  page_size?: number;
  status?: string;
  adapter?: string;
  from_date?: string;
  to_date?: string;
}): Promise<Paginated<Transaction>> {
  const sp = new URLSearchParams();
  if (params?.q) sp.set("q", params.q);
  if (params?.page) sp.set("page", String(params.page));
  if (params?.page_size) sp.set("page_size", String(params.page_size));
  if (params?.status) sp.set("status", params.status);
  if (params?.adapter) sp.set("adapter", params.adapter);
  if (params?.from_date) sp.set("from_date", params.from_date);
  if (params?.to_date) sp.set("to_date", params.to_date);
  const qs = sp.toString();
  return fetchApi<Paginated<Transaction>>(`/transactions${qs ? `?${qs}` : ""}`);
}

/** T008: the dashboard's primary action — create a payment without writing client code. */
export async function simulateTransaction(
  payload: PaymentSimulationRequest
): Promise<PaymentSimulationResponse> {
  return fetchApi<PaymentSimulationResponse>("/transactions/simulate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** T014: project-wide aggregates. Not derivable from a single page of transactions. */
export async function getAnalyticsOverview(): Promise<ProjectAnalyticsOverview> {
  return fetchApi<ProjectAnalyticsOverview>("/analytics/overview");
}

/** T025: diagnose whether the configured callback endpoint is reachable. */
export async function pingWebhook(target_url?: string | null): Promise<WebhookPingResponse> {
  return fetchApi<WebhookPingResponse>("/project/webhook-ping", {
    method: "POST",
    body: JSON.stringify(target_url ? { target_url } : {}),
  });
}

export async function getTransaction(id: string): Promise<Transaction> {
  return fetchApi<Transaction>(`/transactions/${id}`);
}

export async function patchTransaction(
  id: string,
  forced_scenario: ScenarioOutcome | null
): Promise<Transaction> {
  return fetchApi<Transaction>(`/transactions/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ forced_scenario }),
  });
}

export async function deleteTransaction(id: string): Promise<Transaction> {
  return fetchApi<Transaction>(`/transactions/${id}`, {
    method: "DELETE",
  });
}

export async function getProject(): Promise<Project> {
  return fetchApi<Project>("/project");
}

export async function patchProject(updates: Partial<Project>): Promise<Project> {
  return fetchApi<Project>("/project", {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

export async function getAdapters(): Promise<AdapterConfig[]> {
  return fetchApi<AdapterConfig[]>("/adapters");
}

export interface OfferedProvidersResponse {
  providers: string[];
  count: number;
}

export async function getPlatformProviders(): Promise<OfferedProvidersResponse> {
  return fetchApi<OfferedProvidersResponse>("/providers");
}

export async function setPlatformProvider(
  provider: string,
  enabled: boolean
): Promise<OfferedProvidersResponse> {
  return fetchApi<OfferedProvidersResponse>(`/admin/providers/${provider}`, {
    method: "PATCH",
    body: JSON.stringify({ enabled }),
  });
}

export async function getAdminSubscriptions(): Promise<AdminSubscription[]> {
  const res = await fetchApi<{ subscriptions: AdminSubscription[] }>("/admin/subscriptions");
  return res.subscriptions;
}

export async function deactivateAdminSubscription(
  subscriptionId: string
): Promise<{ subscription: AdminSubscription }> {
  return fetchApi<{ subscription: AdminSubscription }>(
    `/admin/subscriptions/${subscriptionId}/deactivate`,
    { method: "POST" }
  );
}

export async function patchAdapter(
  id: string,
  updates: { credentials?: Record<string, unknown> }
): Promise<AdapterConfig> {
  return fetchApi<AdapterConfig>(`/adapters/${id}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

export async function testAdapter(id: string): Promise<{ provider: string; ok: boolean }> {
  return fetchApi<{ provider: string; ok: boolean }>(`/adapters/${id}/test`, {
    method: "POST",
  });
}

export async function listDeliveries(params?: {
  transaction_id?: string;
  result?: string;
  page?: number;
  page_size?: number;
}): Promise<Paginated<WebhookDelivery>> {
  const sp = new URLSearchParams();
  if (params?.transaction_id) sp.set("transaction_id", params.transaction_id);
  if (params?.result) sp.set("result", params.result);
  if (params?.page) sp.set("page", String(params.page));
  if (params?.page_size) sp.set("page_size", String(params.page_size));
  const qs = sp.toString();
  return fetchApi<Paginated<WebhookDelivery>>(`/deliveries${qs ? `?${qs}` : ""}`);
}

export async function retryDelivery(id: string): Promise<WebhookDelivery> {
  return fetchApi<WebhookDelivery>(`/deliveries/${id}/retry`, {
    method: "POST",
  });
}

export async function updateProjectWebhookUrl(webhook_url: string | null): Promise<Project> {
  return fetchApi<Project>("/project/webhook-url", {
    method: "PUT",
    body: JSON.stringify({ webhook_url }),
  });
}

export async function getQuotaMeters(): Promise<QuotaMeters> {
  return fetchApi<QuotaMeters>("/meters?quota=true");
}

export async function getSubscription(): Promise<Subscription> {
  return fetchApi<Subscription>("/billing/subscription");
}

export async function upgradePlan(
  tier: string = "team"
): Promise<{ subscription_id: string; amount_rial: number; authority: string; payment_url: string }> {
  return fetchApi<{ subscription_id: string; amount_rial: number; authority: string; payment_url: string }>(
    "/billing/upgrade",
    {
      method: "POST",
      body: JSON.stringify({ tier }),
    }
  );
}

export async function loginUser(credentials: {
  email: string;
  password: string;
}): Promise<{ user: User; token: string }> {
  return fetchApi<{ user: User; token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export async function sendOtp(data: {
  email: string;
  full_name?: string;
}): Promise<{ status: string; resend_in_seconds: number }> {
  return fetchApi<{ status: string; resend_in_seconds: number }>("/auth/otp/send", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function verifyOtp(data: {
  email: string;
  code: string;
}): Promise<{ verified: boolean; verification_token: string }> {
  return fetchApi<{ verified: boolean; verification_token: string }>("/auth/otp/verify", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function registerUser(data: {
  email: string;
  password: string;
  password_confirmation?: string;
  full_name?: string;
  verification_token?: string;
}): Promise<{ user: User; project: Project; token: string }> {
  return fetchApi<{ user: User; project: Project; token: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function logoutUser(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>("/auth/logout", {
    method: "POST",
  });
}

export async function getMe(): Promise<{ user: User; project: Project }> {
  return fetchApi<{ user: User; project: Project }>("/auth/me");
}



export interface ApiKey {
  id: string;
  name: string;
  last_four: string;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreated extends ApiKey {
  token: string;
}

export async function listApiKeys(): Promise<ApiKey[]> {
  const json = await fetchApi<{ data: ApiKey[] }>("/auth/api-keys");
  return json.data;
}

export async function createApiKey(name: string): Promise<ApiKeyCreated> {
  const json = await fetchApi<{ data: ApiKeyCreated }>("/auth/api-keys", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return json.data;
}

export async function revokeApiKey(id: string): Promise<void> {
  await fetchApi<unknown>(`/auth/api-keys/${id}`, { method: "DELETE" });
}
