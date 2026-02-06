import { useEffect, useState } from "react";
import { getRequest } from "../services/api";
import type { RequestStatus } from "../types";

interface Props {
  requestId: number;
  onComplete: (entityId: string | null) => void;
  onCancel?: () => void;
}

export default function RequestStatusPoll({ requestId, onComplete, onCancel }: Props) {
  const [status, setStatus] = useState<RequestStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const req = await getRequest(requestId);
        if (cancelled) return;
        setStatus(req.status);
        setErrorMessage(req.error_message ?? null);
        if (req.status === "COMPLETED") {
          onComplete(req.entity_id ?? null);
          return;
        }
        if (req.status === "FAILED") {
          onComplete(null);
          return;
        }
        setTimeout(poll, 2000);
      } catch (e) {
        if (!cancelled) setErrorMessage(String(e));
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [requestId, onComplete]);

  return (
    <div>
      <p>Request #{requestId}: {status ?? "…"}</p>
      {errorMessage && <p className="error">{errorMessage}</p>}
      {onCancel && (
        <button type="button" onClick={onCancel}>
          Cancel
        </button>
      )}
    </div>
  );
}
