import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listDocuments, indexDocumentAsync } from "../services/api";
import RequestStatusPoll from "../components/RequestStatusPoll";

export default function DocumentManagement() {
  const [requestId, setRequestId] = useState<number | null>(null);
  const queryClient = useQueryClient();

  const { data: documents, isLoading, error } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
  });

  const indexMutation = useMutation({
    mutationFn: (file: File) => indexDocumentAsync(file),
    onSuccess: (data) => setRequestId(data.id),
  });

  const onRequestComplete = () => {
    queryClient.invalidateQueries({ queryKey: ["documents"] });
    setRequestId(null);
  };

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) indexMutation.mutate(file);
    e.target.value = "";
  };

  if (isLoading) return <p>Loading documents…</p>;
  if (error) return <p className="error">Error: {String(error)}</p>;

  return (
    <section>
      <h2>Document management</h2>
      <p>Upload PDFs to index for RAG. Indexed documents appear below.</p>
      {requestId ? (
        <RequestStatusPoll
          requestId={requestId}
          onComplete={onRequestComplete}
          onCancel={() => setRequestId(null)}
        />
      ) : (
        <p>
          <label>
            Upload file:{" "}
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleUpload}
              disabled={indexMutation.isPending}
            />
          </label>
        </p>
      )}
      <h3>Indexed documents</h3>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {(documents ?? []).map((d) => (
          <li key={d.id} style={{ marginBottom: "0.5rem" }}>
            {d.filename} — sections: {d.chunk_count_section}, citations: {d.chunk_count_citation} —{" "}
            <span style={{ fontSize: "0.9rem", color: "#666" }}>
              {d.indexed_at ? new Date(d.indexed_at).toLocaleString() : ""}
            </span>
          </li>
        ))}
      </ul>
      {(!documents || documents.length === 0) && <p>No documents indexed yet.</p>}
    </section>
  );
}
