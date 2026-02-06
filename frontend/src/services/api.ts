import type {
  RequestInfo,
  DocumentRegistryItem,
  ProjectListItem,
  ProjectDetail,
  AnswerInfo,
  AnswerStatus,
  EvaluationReport,
} from "../types";

const API_BASE =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "" : "http://localhost:8000");

async function fetchApi<T>(
  path: string,
  options?: RequestInit & { params?: Record<string, string | number> }
): Promise<T> {
  const { params, ...rest } = options ?? {};
  const base =
    typeof window !== "undefined" ? window.location.origin : "http://localhost:8000";
  const pathWithBase = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const url = new URL(pathWithBase, base);
  if (params) {
    Object.entries(params).forEach(([k, v]) =>
      url.searchParams.set(k, String(v))
    );
  }
  const res = await fetch(url.toString(), {
    ...rest,
    headers: { "Content-Type": "application/json", ...rest.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0")
    return undefined as T;
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<{ status: string }> {
  return fetchApi("/health");
}

export async function getRequest(requestId: number): Promise<RequestInfo> {
  return fetchApi(`/api/requests/${requestId}`);
}

export async function listProjects(): Promise<ProjectListItem[]> {
  return fetchApi("/api/projects/list");
}

export async function getProject(projectId: number): Promise<ProjectDetail> {
  return fetchApi(`/api/projects/${projectId}`);
}

export async function getProjectStatus(
  projectId: number
): Promise<{ project_id: number; status: string }> {
  return fetchApi(`/api/projects/${projectId}/status`);
}

export async function createProjectAsync(
  name: string,
  file: File
): Promise<RequestInfo> {
  const form = new FormData();
  form.set("name", name);
  form.set("file", file);
  const url = `${API_BASE}/api/projects/create-async`;
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
  return res.json() as Promise<RequestInfo>;
}

export async function listDocuments(): Promise<DocumentRegistryItem[]> {
  return fetchApi("/api/documents");
}

export async function indexDocumentAsync(file: File): Promise<RequestInfo> {
  const form = new FormData();
  form.set("file", file);
  const url = `${API_BASE}/api/documents/index-async`;
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
  return res.json() as Promise<RequestInfo>;
}

export async function getAnswersByProject(
  projectId: number
): Promise<AnswerInfo[]> {
  return fetchApi(`/api/answers/by-project/${projectId}`);
}

export async function getAnswerByQuestion(
  questionId: number
): Promise<AnswerInfo | null> {
  return fetchApi(`/api/answers/by-question/${questionId}`);
}

export async function generateAllAnswersAsync(
  projectId: number
): Promise<RequestInfo> {
  return fetchApi(
    `/api/answers/generate-all-async?project_id=${projectId}`,
    { method: "POST" }
  );
}

export async function updateAnswer(
  answerId: number,
  body: { status?: AnswerStatus; manual_answer_text?: string; human_answer_text?: string }
): Promise<AnswerInfo> {
  return fetchApi(`/api/answers/update?answer_id=${answerId}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function runEvaluation(projectId: number): Promise<{
  id: number;
  project_id: number;
  created_at: string | null;
  results: unknown[];
}> {
  return fetchApi(`/api/evaluation/run?project_id=${projectId}`, {
    method: "POST",
  });
}

export async function getEvaluationReport(
  projectId: number,
  runId?: number
): Promise<EvaluationReport | { message: string; results: []; aggregate_score: null }> {
  const q = runId != null ? `?run_id=${runId}` : "";
  return fetchApi(`/api/evaluation/report?project_id=${projectId}${q}`);
}
