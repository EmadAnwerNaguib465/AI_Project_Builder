export type AgentName = "supervisor" | "research" | "rag" | "architect" | "critic" | "report";

export interface ProjectReport {
  project_title: string;
  executive_summary: string;
  objectives: string[];
  technical_architecture: string;
  dataset_plan: string;
  model_plan: string;
  implementation_roadmap: string[];
  risks_and_mitigations: string[];
  success_metrics: string[];
  estimated_timeline_weeks: number;
  required_skills: string[];
  recommended_tools: string[];
  revision_count: number;
  sources: string[];
}

export type PipelineEvent =
  | { type: "started" }
  | { type: "step"; node: AgentName; revision_count: number | null; critic_status: "PASS" | "REVISE" | null; next_agent: string | null }
  | { type: "complete"; report: ProjectReport }
  | { type: "error"; message: string };

export const AGENTS: { id: AgentName; label: string; detail: string }[] = [
  { id: "supervisor", label: "Brief", detail: "Requirements" },
  { id: "research", label: "Research", detail: "Sources & datasets" },
  { id: "rag", label: "Context", detail: "Knowledge base" },
  { id: "architect", label: "Architecture", detail: "System design" },
  { id: "critic", label: "Review", detail: "Quality check" },
  { id: "report", label: "Plan", detail: "Final report" },
];
