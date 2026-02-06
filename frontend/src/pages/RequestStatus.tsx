import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRequest } from "../services/api";

export default function RequestStatus() {
  const [requestId, setRequestId] = useState("");
  const id = requestId ? parseInt(requestId, 10) : null;

  const { data: req, isLoading, error } = useQuery({
    queryKey: ["request", id],
    queryFn: () => getRequest(id!),
    enabled: id != null && Number.isInteger(id),
  });

  return (
    <section>
      <h2>Request status</h2>
      <p>Check status of an async task (e.g. index, create project, generate answers).</p>
      <label>
        Request ID:{" "}
        <input
          type="number"
          value={requestId}
          onChange={(e) => setRequestId(e.target.value)}
          min={1}
          style={{ width: "6rem" }}
        />
      </label>
      {id != null && Number.isInteger(id) && (
        <div style={{ marginTop: "1rem" }}>
          {isLoading && <p>Loading…</p>}
          {error && <p className="error">{String(error)}</p>}
          {req && (
            <pre style={{ background: "#f5f5f5", padding: "1rem", overflow: "auto" }}>
              {JSON.stringify(req, null, 2)}
            </pre>
          )}
        </div>
      )}
    </section>
  );
}
