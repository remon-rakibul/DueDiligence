import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateAnswer } from "../services/api";
import type { QuestionInfo } from "../types";
import type { AnswerInfo } from "../types";

interface Props {
  question: QuestionInfo;
  answer: AnswerInfo | null;
  projectId: number;
  onUpdate: () => void;
}

export default function QuestionReview({ question, answer, projectId, onUpdate }: Props) {
  const [manualText, setManualText] = useState(answer?.manual_answer_text ?? "");
  const [humanText, setHumanText] = useState(answer?.human_answer_text ?? "");
  useEffect(() => {
    setManualText(answer?.manual_answer_text ?? "");
    setHumanText(answer?.human_answer_text ?? "");
  }, [answer?.manual_answer_text, answer?.human_answer_text]);
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (payload: {
      status?: "CONFIRMED" | "REJECTED" | "MANUAL_UPDATED";
      manual_answer_text?: string;
      human_answer_text?: string;
    }) => updateAnswer(answer!.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["answers", projectId] });
      onUpdate();
    },
  });

  const displayText = answer?.answer_text ?? answer?.ai_answer_text ?? "—";

  return (
    <div>
      <div style={{ fontWeight: 600 }}>{question.section_title ?? `Q${question.order_index}`}</div>
      <p style={{ margin: "0.25rem 0" }}>{question.question_text}</p>
      {answer ? (
        <>
          <p style={{ color: "#444", fontSize: "0.95rem" }}>
            AI answer: {displayText}
            {answer.confidence_score != null && (
              <span style={{ marginLeft: "0.5rem", color: "#666" }}>
                (confidence: {(answer.confidence_score * 100).toFixed(0)}%)
              </span>
            )}
          </p>
          {answer.citations?.length > 0 && (
            <details style={{ marginTop: "0.5rem" }}>
              <summary>Citations</summary>
              <ul style={{ fontSize: "0.9rem", color: "#666" }}>
                {answer.citations.map((c) => (
                  <li key={c.id}>{c.snippet ?? c.chunk_id}</li>
                ))}
              </ul>
            </details>
          )}
          <div style={{ marginTop: "0.5rem" }}>
            <label>
              Manual edit:{" "}
              <input
                type="text"
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                style={{ width: "100%", maxWidth: "24rem" }}
              />
            </label>
          </div>
          <div style={{ marginTop: "0.5rem" }}>
            <button
              type="button"
              onClick={() => updateMutation.mutate({ status: "CONFIRMED" })}
              disabled={updateMutation.isPending}
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => updateMutation.mutate({ status: "REJECTED" })}
              disabled={updateMutation.isPending}
            >
              Reject
            </button>
            <button
              type="button"
              onClick={() =>
                updateMutation.mutate({
                  status: "MANUAL_UPDATED",
                  manual_answer_text: manualText || undefined,
                })
              }
              disabled={updateMutation.isPending}
            >
              Save manual
            </button>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label>
              Human answer (for evaluation):{" "}
              <input
                type="text"
                value={humanText}
                onChange={(e) => setHumanText(e.target.value)}
                placeholder="Ground truth for evaluation report"
                style={{ width: "100%", maxWidth: "24rem" }}
              />
            </label>
            <button
              type="button"
              onClick={() => updateMutation.mutate({ human_answer_text: humanText || undefined })}
              disabled={updateMutation.isPending}
              style={{ marginLeft: "0.5rem" }}
            >
              Save human answer
            </button>
          </div>
          <span style={{ marginLeft: "0.5rem", fontSize: "0.9rem", color: "#666" }}>
            Status: {answer.status}
          </span>
        </>
      ) : (
        <p style={{ color: "#888" }}>No answer yet. Run “Generate all answers” for this project.</p>
      )}
    </div>
  );
}
