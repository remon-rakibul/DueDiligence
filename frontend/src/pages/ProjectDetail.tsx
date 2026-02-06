import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getProject,
  getAnswersByProject,
  generateAllAnswersAsync,
} from "../services/api";
import QuestionReview from "../components/QuestionReview";
import RequestStatusPoll from "../components/RequestStatusPoll";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const id = projectId ? parseInt(projectId, 10) : NaN;
  const queryClient = useQueryClient();
  const [generateRequestId, setGenerateRequestId] = useState<number | null>(null);

  const projectQuery = useQuery({
    queryKey: ["project", id],
    queryFn: () => getProject(id),
    enabled: Number.isInteger(id),
    refetchInterval: (q) => (q.state.data?.status === "GENERATING" ? 5000 : false),
  });

  const answersQuery = useQuery({
    queryKey: ["answers", id],
    queryFn: () => getAnswersByProject(id),
    enabled: Number.isInteger(id),
    refetchInterval: generateRequestId != null ? 5000 : false,
  });

  const generateMutation = useMutation({
    mutationFn: () => generateAllAnswersAsync(id),
    onSuccess: (data) => {
      setGenerateRequestId(data.id);
    },
  });

  const onGenerateRequestComplete = () => {
    setGenerateRequestId(null);
    queryClient.invalidateQueries({ queryKey: ["project", id] });
    queryClient.invalidateQueries({ queryKey: ["answers", id] });
  };

  if (projectQuery.isLoading || !projectQuery.data) {
    return projectQuery.isLoading ? <p>Loading…</p> : <p>Project not found.</p>;
  }

  const project = projectQuery.data;
  const answers = answersQuery.data ?? [];
  const answersByQ = Object.fromEntries(answers.map((a) => [a.question_id, a]));

  return (
    <section>
      <nav style={{ marginBottom: "1rem" }}>
        <Link to="/">← Projects</Link>
      </nav>
      <h2>{project.name}</h2>
      <p>Status: {project.status}</p>
      {project.status === "GENERATING" && (
        <p style={{ color: "#666", fontSize: "0.95rem" }}>
          Answer generation runs one question at a time and can take several minutes for large questionnaires. This page will update when it finishes.
        </p>
      )}
      {generateRequestId != null && (
        <RequestStatusPoll
          requestId={generateRequestId}
          onComplete={onGenerateRequestComplete}
          onCancel={() => setGenerateRequestId(null)}
        />
      )}
      <p>
        <Link to={`/projects/${id}/evaluation`}>Evaluation report</Link>
      </p>
      {project.status !== "COMPLETE" && project.status !== "GENERATING" && (
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
        >
          {generateMutation.isPending ? "Generating…" : "Generate all answers"}
        </button>
      )}
      {project.status !== "COMPLETE" && project.status !== "GENERATING" && (
        <p style={{ marginTop: "0.5rem", color: "#666", fontSize: "0.9rem" }}>
          May take several minutes for questionnaires with many questions.
        </p>
      )}
      <hr style={{ margin: "1rem 0" }} />
      <h3>Questions & answers</h3>
      {project.questions.length === 0 ? (
        <p>
          No questions were extracted from the questionnaire PDF. This can happen if the
          file was not a questionnaire (e.g. use the <strong>ILPA Due Diligence
          Questionnaire</strong> PDF when creating the project), or the format was not
          recognized. Try creating a new project and uploading the questionnaire PDF again.
        </p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {project.questions.map((q) => (
            <li key={q.id} style={{ marginBottom: "1.5rem", borderBottom: "1px solid #eee", paddingBottom: "1rem" }}>
              <QuestionReview
                question={q}
                answer={answersByQ[q.id] ?? null}
                projectId={id}
                onUpdate={() => {
                  queryClient.invalidateQueries({ queryKey: ["answers", id] });
                }}
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
