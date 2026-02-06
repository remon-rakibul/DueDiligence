import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createProjectAsync } from "../services/api";
import RequestStatusPoll from "../components/RequestStatusPoll";

export default function CreateProject() {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [requestId, setRequestId] = useState<number | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Choose a questionnaire file");
      return createProjectAsync(name.trim() || "New Project", file);
    },
    onSuccess: (data) => {
      setRequestId(data.id);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate();
  };

  const onRequestComplete = (entityId: string | null) => {
    queryClient.invalidateQueries({ queryKey: ["projects"] });
    if (entityId) navigate(`/projects/${entityId}`);
    setRequestId(null);
  };

  return (
    <section>
      <h2>Create project</h2>
      {requestId ? (
        <RequestStatusPoll
          requestId={requestId}
          onComplete={onRequestComplete}
          onCancel={() => setRequestId(null)}
        />
      ) : (
        <form onSubmit={handleSubmit} style={{ maxWidth: "24rem" }}>
          <div style={{ marginBottom: "0.75rem" }}>
            <label htmlFor="name">Project name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ display: "block", width: "100%", marginTop: "0.25rem" }}
            />
          </div>
          <div style={{ marginBottom: "0.75rem" }}>
            <label htmlFor="file">Questionnaire PDF</label>
            <input
              id="file"
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              style={{ display: "block", marginTop: "0.25rem" }}
            />
          </div>
          <button type="submit" disabled={createMutation.isPending || !file}>
            {createMutation.isPending ? "Creating…" : "Create project"}
          </button>
          {createMutation.isError && (
            <p className="error" style={{ marginTop: "0.5rem" }}>
              {String(createMutation.error)}
            </p>
          )}
        </form>
      )}
    </section>
  );
}
