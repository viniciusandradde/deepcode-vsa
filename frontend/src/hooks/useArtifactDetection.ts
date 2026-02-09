import { useCallback } from "react";
import type { Artifact, ArtifactType } from "@/state/artifact-types";

/**
 * Patterns for detecting report-like sections in LLM-generated content.
 * Each pattern defines a regex, the artifact type, and a title extractor.
 */
interface DetectionRule {
  /** Regex to test against the full message content. */
  pattern: RegExp;
  /** Artifact type to assign. */
  type: ArtifactType;
  /** Extract title from the content (or use a default). */
  title: (content: string) => string;
  /**
   * Extract the artifact body from the full message.
   * Returns [artifactContent, remainingContent].
   */
  extract: (content: string) => [string, string] | null;
}

const SECTION_RULES: DetectionRule[] = [
  // RCA / 5 Porquês analysis
  {
    pattern: /##?\s*(An[aá]lise\s+de\s+Causa\s+Raiz|RCA|Root\s+Cause|5\s+Porqu[eê]s)/i,
    type: "rca_analysis",
    title: (content) => {
      const match = content.match(/##?\s*(An[aá]lise\s+de\s+Causa\s+Raiz|RCA[^#\n]*)/i);
      return match ? match[1].trim() : "Análise de Causa Raiz";
    },
    extract: (content) => extractSection(content, /##?\s*(An[aá]lise\s+de\s+Causa\s+Raiz|RCA|Root\s+Cause|5\s+Porqu[eê]s)/i),
  },
  // 5W2H analysis
  {
    pattern: /##?\s*(5W2H|An[aá]lise\s+5W2H)/i,
    type: "fivew2h_analysis",
    title: (content) => {
      const match = content.match(/##?\s*(5W2H[^#\n]*|An[aá]lise\s+5W2H[^#\n]*)/i);
      return match ? match[1].trim() : "Análise 5W2H";
    },
    extract: (content) => extractSection(content, /##?\s*(5W2H|An[aá]lise\s+5W2H)/i),
  },
  // ITIL Classification table
  {
    pattern: /##?\s*(CLASSIFICA[CÇ][AÃ]O\s+ITIL|Classifica[cç][aã]o\s+ITIL)/i,
    type: "itil_classification",
    title: () => "Classificação ITIL",
    extract: (content) => extractSection(content, /##?\s*(CLASSIFICA[CÇ][AÃ]O\s+ITIL|Classifica[cç][aã]o\s+ITIL)/i),
  },
];

/**
 * Extract a markdown section starting at the matched heading until the next
 * heading of equal or higher level, or end of content.
 * Returns [sectionContent, remainingContent] or null.
 */
function extractSection(content: string, headingPattern: RegExp): [string, string] | null {
  const match = content.match(headingPattern);
  if (!match || match.index === undefined) return null;

  const startIdx = match.index;

  // Determine heading level
  const headingLine = content.slice(startIdx).split("\n")[0];
  const level = (headingLine.match(/^#+/) || ["##"])[0].length;

  // Find the next heading of same or higher level
  const afterHeading = content.slice(startIdx + headingLine.length + 1);
  const nextHeadingRegex = new RegExp(`^#{1,${level}}\\s`, "m");
  const nextMatch = afterHeading.match(nextHeadingRegex);

  let endIdx: number;
  if (nextMatch && nextMatch.index !== undefined) {
    endIdx = startIdx + headingLine.length + 1 + nextMatch.index;
  } else {
    endIdx = content.length;
  }

  const section = content.slice(startIdx, endIdx).trim();

  // Only extract if section is substantial (>200 chars with tables or multiple lines)
  if (section.length < 200) return null;

  const remaining = (content.slice(0, startIdx) + content.slice(endIdx)).trim();
  return [section, remaining];
}

/**
 * Hook that detects report-like sections in LLM content
 * and converts them into Artifact objects.
 */
export function useArtifactDetection() {
  const detectArtifacts = useCallback(
    (
      content: string,
      sessionId: string,
      messageId: string,
    ): { artifacts: Artifact[]; cleanedContent: string } => {
      const artifacts: Artifact[] = [];
      let remaining = content;

      for (const rule of SECTION_RULES) {
        if (!rule.pattern.test(remaining)) continue;

        const result = rule.extract(remaining);
        if (!result) continue;

        const [sectionContent, leftover] = result;

        const artifact: Artifact = {
          id: `art-llm-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          sessionId,
          messageId,
          type: rule.type,
          title: rule.title(sectionContent),
          content: sectionContent,
          createdAt: Date.now(),
          source: "llm",
        };

        artifacts.push(artifact);
        remaining = leftover;
      }

      return { artifacts, cleanedContent: remaining };
    },
    [],
  );

  return { detectArtifacts };
}
