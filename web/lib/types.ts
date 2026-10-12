export const AGENTS = [
  { id: "supervisor", label: "Supervisor", detail: "Clarifies the project brief" },
  { id: "research", label: "Researcher", detail: "Finds datasets and sources" },
  { id: "rag", label: "Knowledge Base", detail: "Retrieves useful AI knowledge" },
  { id: "architect", label: "Architect", detail: "Designs the technical plan" },
  { id: "critic", label: "Reviewer", detail: "Checks and improves the plan" },
  { id: "report", label: "Planner", detail: "Builds your final blueprint" },
] as const;

export type AgentName = (typeof AGENTS)[number]["id"];
export type ProjectReport = {
  project_title: string; executive_summary: string; objectives: string[];
  technical_architecture: string; dataset_plan: string; model_plan: string;
  implementation_roadmap: string[]; risks_and_mitigations: string[];
  success_metrics: string[]; estimated_timeline_weeks: number;
  required_skills: string[]; recommended_tools: string[]; revision_count: number;
  sources: string[];
  dataset_recommendations?: { url: string; provider: string; name: string; description: string; relevance: string; data_type: string; size: string; license: string; access: string; discovery_source: string }[];
  dataset_discovery_note?: string;
};
export type PipelineEvent =
  | { type: "started" }
  | { type: "step"; node: AgentName; revision_count: number | null; critic_status: string | null; next_agent: string | null }
  | { type: "complete"; report: ProjectReport }
  | { type: "error"; message: string };
