/**
 * Converts markdown text to styled HTML suitable for rich clipboard copy.
 * Supports: headings, bold, italic, code, links, tables, ordered/unordered lists, code blocks.
 */
export function markdownToHtml(markdown: string): string {
  let text = markdown;
  const codeBlocks: string[] = [];

  const escapeHtml = (value: string) =>
    value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  text = text.replace(/```[\s\S]*?```/g, (match) => {
    const index = codeBlocks.length;
    codeBlocks.push(match);
    return `__CODE_BLOCK_${index}__`;
  });

  text = text.replace(
    /^###\s+(.*)$/gm,
    '<h3 style="margin:12px 0 8px;font-size:18px;font-weight:600;">$1</h3>'
  );
  text = text.replace(
    /^##\s+(.*)$/gm,
    '<h2 style="margin:14px 0 10px;font-size:20px;font-weight:700;">$1</h2>'
  );
  text = text.replace(
    /^#\s+(.*)$/gm,
    '<h1 style="margin:16px 0 12px;font-size:22px;font-weight:700;">$1</h1>'
  );

  const lines = text.split("\n");
  const output: string[] = [];
  let inList = false;
  let listType: "ul" | "ol" | null = null;

  const isTableSeparator = (line: string) =>
    /^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*$/.test(line);

  const normalizeRowLine = (line: string) => {
    const trimmed = line.trim();
    if (!trimmed.includes("|")) return trimmed;
    return trimmed.replace(/^\|/, "").replace(/\|$/, "");
  };

  const parseTableRow = (line: string) =>
    normalizeRowLine(line)
      .split("|")
      .map((cell) => escapeHtml(cell.trim()));

  const parseAlignments = (line: string) =>
    normalizeRowLine(line)
      .split("|")
      .map((cell) => {
        const trimmed = cell.trim();
        if (trimmed.startsWith(":") && trimmed.endsWith(":")) return "center";
        if (trimmed.endsWith(":")) return "right";
        if (trimmed.startsWith(":")) return "left";
        return "left";
      });

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const nextLine = lines[i + 1];

    if (line.includes("|") && nextLine && isTableSeparator(nextLine)) {
      if (inList) {
        output.push("</ul>");
        inList = false;
      }

      const headers = parseTableRow(line);
      const alignments = parseAlignments(nextLine);
      const rows: string[] = [];
      i += 2;
      while (i < lines.length && lines[i].includes("|")) {
        const cells = parseTableRow(lines[i]);
        rows.push(
          `<tr>${cells
            .map((c, idx) => {
              const align = alignments[idx] || "left";
              return `<td style="border:1px solid #e2e8f0;padding:6px 8px;text-align:${align};vertical-align:top;">${c}</td>`;
            })
            .join("")}</tr>`
        );
        i += 1;
      }
      i -= 1;

      output.push(
        `<table style="border-collapse:collapse;width:100%;margin:10px 0;"><thead><tr>${headers
          .map((h, idx) => {
            const align = alignments[idx] || "left";
            return `<th style="border:1px solid #cbd5f5;padding:6px 8px;text-align:${align};background:#f8fafc;font-weight:600;">${h}</th>`;
          })
          .join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`
      );
      continue;
    }

    const unorderedMatch = /^\s*[-*]\s+(.*)/.exec(line);
    const orderedMatch = /^\s*\d+\.\s+(.*)/.exec(line);
    if (unorderedMatch || orderedMatch) {
      const nextType: "ul" | "ol" = orderedMatch ? "ol" : "ul";
      if (!inList || listType !== nextType) {
        if (inList) output.push(`</${listType}>`);
        output.push(
          nextType === "ol"
            ? '<ol style="margin:8px 0 8px 20px;">'
            : '<ul style="margin:8px 0 8px 20px;">'
        );
        inList = true;
        listType = nextType;
      }
      output.push(`<li>${(orderedMatch || unorderedMatch)?.[1] || ""}</li>`);
      continue;
    }

    if (inList) {
      output.push(`</${listType}>`);
      inList = false;
      listType = null;
    }
    output.push(line);
  }

  if (inList) output.push(`</${listType}>`);

  text = output.join("\n");
  text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/__(.+?)__/g, "<strong>$1</strong>");
  text = text.replace(/\*(.+?)\*/g, "<em>$1</em>");
  text = text.replace(/_(.+?)_/g, "<em>$1</em>");
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  text = text.replace(
    /\[([^\]]+)]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" style="color:#0f172a;text-decoration:underline;" target="_blank" rel="noreferrer">$1</a>'
  );

  text = text
    .split(/\n\n+/)
    .map((block) => {
      if (
        block.trim().startsWith("<h") ||
        block.trim().startsWith("<ul") ||
        block.trim().startsWith("<ol") ||
        block.trim().startsWith("<table")
      ) {
        return block;
      }
      return `<p style="margin:8px 0;">${block.replace(/\n/g, "<br />")}</p>`;
    })
    .join("\n");

  text = text.replace(/__CODE_BLOCK_(\d+)__/g, (_, idx) => {
    const raw = codeBlocks[Number(idx)] || "";
    const content = raw.replace(/^```[a-zA-Z0-9-]*\n?/, "").replace(/```$/, "");
    return `<pre><code>${content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</code></pre>`;
  });

  return `<!DOCTYPE html><html><body>${text}</body></html>`;
}
