import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getEvaluationReport, runEvaluation } from "../services/api";

export default function EvaluationReport() {
  const { projectId } = useParams<{ projectId: string }>();
  const id = projectId ? parseInt(projectId, 10) : NaN;
  const queryClient = useQueryClient();

  const reportQuery = useQuery({
    queryKey: ["evaluation", id],
    queryFn: () => getEvaluationReport(id),
    enabled: Number.isInteger(id),
  });

  const runMutation = useMutation({
    mutationFn: () => runEvaluation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluation", id] });
    },
  });

  if (reportQuery.isLoading) return <p>Loading…</p>;
  const data = reportQuery.data;
  if (!data || "message" in data) {
    return (
      <section>
        <nav style={{ marginBottom: "1rem" }}>
          <Link to={`/projects/${id}`}>← Project</Link>
        </nav>
        <h2>Evaluation report</h2>
        <p>{"message" in data ? data.message : "No report."}</p>
        <button onClick={() => runMutation.mutate()} disabled={runMutation.isPending}>
          {runMutation.isPending ? "Running…" : "Run evaluation"}
        </button>
      </section>
    );
  }

  return (
    <section>
      <nav style={{ marginBottom: "1rem" }}>
        <Link to={`/projects/${id}`}>← Project</Link>
      </nav>
      <h2>Evaluation report</h2>
      <p>Run: {data.run_id} — {data.created_at ? new Date(data.created_at).toLocaleString() : ""}</p>
      <p>Aggregate similarity score: {data.aggregate_score ?? "—"}</p>
      <button onClick={() => runMutation.mutate()} disabled={runMutation.isPending}>
        {runMutation.isPending ? "Running…" : "Run new evaluation"}
      </button>
      <h3>Results</h3>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {data.results.map((r, i) => (
          <li key={i} style={{ marginBottom: "1rem", borderBottom: "1px solid #eee", paddingBottom: "0.5rem" }}>
            <strong>Q{r.question_id}</strong> — score: {r.similarity_score ?? "—"}
            <div style={{ fontSize: "0.9rem", color: "#444" }}>AI: {r.ai_answer ?? "—"}</div>
            <div style={{ fontSize: "0.9rem", color: "#444" }}>Human: {r.human_answer ?? "—"}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}
