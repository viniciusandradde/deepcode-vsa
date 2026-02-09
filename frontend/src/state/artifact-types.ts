export type ArtifactType =
  | "glpi_report"
  | "zabbix_report"
  | "linear_report"
  | "dashboard"
  | "itil_classification"
  | "rca_analysis"
  | "fivew2h_analysis"
  | "generic_report";

export type ArtifactSource = "rule-based" | "llm";

export interface Artifact {
  id: string;
  sessionId: string;
  messageId: string;
  type: ArtifactType;
  title: string;
  content: string;
  createdAt: number;
  source: ArtifactSource;
  intent?: string;
}

/** Data emitted in artifact_start SSE event. */
export interface ArtifactStartData {
  artifact_id: string;
  title: string;
  artifact_type: ArtifactType;
  intent: string;
  source: ArtifactSource;
}
