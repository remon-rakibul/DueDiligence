import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { getHealth } from "./services/api";
import ProjectList from "./pages/ProjectList";
import ProjectDetail from "./pages/ProjectDetail";
import CreateProject from "./pages/CreateProject";
import DocumentManagement from "./pages/DocumentManagement";
import EvaluationReport from "./pages/EvaluationReport";
import RequestStatus from "./pages/RequestStatus";

const queryClient = new QueryClient();

function Layout({ children }: { children: React.ReactNode }) {
  const [backendStatus, setBackendStatus] = useState<"checking" | "ok" | "error">("checking");

  useEffect(() => {
    getHealth()
      .then(() => setBackendStatus("ok"))
      .catch(() => setBackendStatus("error"));
  }, []);

  return (
    <div style={{ fontFamily: "system-ui", maxWidth: "56rem", margin: "0 auto", padding: "1rem" }}>
      <header style={{ borderBottom: "1px solid #eee", paddingBottom: "0.75rem", marginBottom: "1rem" }}>
        <h1 style={{ margin: 0 }}>
          <Link to="/" style={{ color: "inherit", textDecoration: "none" }}>
            Questionnaire Agent
          </Link>
        </h1>
        <nav style={{ marginTop: "0.5rem" }}>
          <Link to="/" style={{ marginRight: "1rem" }}>Projects</Link>
          <Link to="/create" style={{ marginRight: "1rem" }}>Create project</Link>
          <Link to="/documents" style={{ marginRight: "1rem" }}>Documents</Link>
          <Link to="/requests" style={{ marginRight: "1rem" }}>Request status</Link>
        </nav>
        <p style={{ margin: "0.5rem 0 0", fontSize: "0.9rem", color: "#666" }}>
          Backend: {backendStatus === "checking" ? "checking…" : backendStatus === "ok" ? "connected" : "disconnected"}
        </p>
      </header>
      <main>{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<ProjectList />} />
            <Route path="/create" element={<CreateProject />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            <Route path="/projects/:projectId/evaluation" element={<EvaluationReport />} />
            <Route path="/documents" element={<DocumentManagement />} />
            <Route path="/requests" element={<RequestStatus />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
