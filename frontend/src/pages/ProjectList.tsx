import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listProjects } from "../services/api";

export default function ProjectList() {
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  if (isLoading) return <p>Loading projects…</p>;
  if (error) return <p className="error">Error: {String(error)}</p>;

  return (
    <section>
      <h2>Projects</h2>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {(projects ?? []).map((p) => (
          <li key={p.id} style={{ marginBottom: "0.5rem" }}>
            <Link to={`/projects/${p.id}`}>
              {p.name}
            </Link>
            <span style={{ marginLeft: "0.5rem", color: "#666", fontSize: "0.9rem" }}>
              — {p.status}
            </span>
          </li>
        ))}
      </ul>
      {(!projects || projects.length === 0) && <p>No projects yet. Create one from the nav.</p>}
    </section>
  );
}
