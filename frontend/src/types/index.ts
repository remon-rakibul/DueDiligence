export type ProjectStatus =
  | "PENDING"
  | "INDEXING"
  | "READY"
  | "OUTDATED"
  | "GENERATING"
  | "COMPLETE";

export type AnswerStatus =
  | "PENDING"
  | "CONFIRMED"
  | "REJECTED"
  | "MANUAL_UPDATED"
  | "MISSING_DATA";

export type RequestType =
  | "create_project"
  | "update_project"
  | "index_document"
  | "generate_answers";

export type RequestStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface Citation {
  id: number;
  answer_id: number;
  chunk_id: string | null;
  document_id: string | null;
  snippet: string | null;
  bounding_box_ref: string | null;
  order_index: number;
}

export interface RequestInfo {
  id: number;
  type: RequestType;
  status: RequestStatus;
  entity_id: string | null;
  result_payload: string | null;
  error_message: string | null;
  created_at: string;
}

export interface DocumentRegistryItem {
  id: number;
  document_id: string;
  filename: string;
  indexed_at: string;
  chunk_count_section: number;
  chunk_count_citation: number;
  created_at: string;
}

export interface ProjectListItem {
  id: number;
  name: string;
  status: ProjectStatus;
  scope: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface QuestionInfo {
  id: number;
  section_id: string | null;
  section_title: string | null;
  question_text: string;
  order_index: number;
}

export interface ProjectDetail {
  id: number;
  name: string;
  questionnaire_document_id: string | null;
  scope: string;
  status: ProjectStatus;
  created_at: string | null;
  updated_at: string | null;
  questions: QuestionInfo[];
}

export interface AnswerInfo {
  id: number;
  question_id: number;
  answer_text: string | null;
  is_answerable: boolean;
  confidence_score: number | null;
  status: AnswerStatus;
  ai_answer_text: string | null;
  manual_answer_text: string | null;
  human_answer_text: string | null;
  created_at: string;
  updated_at: string;
  citations: Citation[];
}

export interface EvaluationResultItem {
  question_id: number;
  ai_answer: string | null;
  human_answer: string | null;
  similarity_score: number | null;
  details: unknown;
}

export interface EvaluationReport {
  project_id: number;
  run_id: number;
  created_at: string | null;
  aggregate_score: number | null;
  results: EvaluationResultItem[];
}
