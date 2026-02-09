# Research & Proposal: Chat Export and Artifacts System

## 1. Chat Export (DOCX, MD, PDF)

### Analysis

The goal is to export the conversation history from the chat interface to portable formats.

- **Current State**: Messages are stored in PostgreSQL (JSONB) and rendered via `react-markdown`.
- **Challenge**: Converting dynamic React/Markdown content to static files (PDF/DOCX) faithfully.

### Recommended Strategy: Server-Side Generation

Generating files on the backend is more robust and consistent than client-side PDF generation (which often suffers from CSS print issues).

#### Technologies

1. **Markdown (MD)**:
    - **Implementation**: Trivial. Concatenate messages with `\n---\n` separators.
    - **Cost**: Zero logic.

2. **PDF**:
    - **Tool**: **WeasyPrint** (Python).
    - **Why**: It converts HTML + CSS to PDF with high fidelity. Supports standard CSS/Page-media.
    - **Flow**: `Markdown` -> `markdown2` (Python lib to get HTML) -> `WeasyPrint` -> PDF.
    - **Pros**: Pure Python (mostly), highly customizable styling via CSS.

3. **DOCX**:
    - **Tool**: **python-docx** or **pypandoc**.
    - **Recommendation**: **pypandoc** (wrapper for Pandoc) is the gold standard but requires installing the `pandoc` binary in the Docker container (`Dockerfile.backend`).
    - **Alternative**: `htmldocx` (converts HTML to DOCX). Less perfect but pure Python/JS options exist.
    - **Decision**: If `pandoc` installation is acceptable, use it. Otherwise, `markdown2` + `htmldocx`.

### Proposed API Endpoint

```python
GET /api/v1/threads/{thread_id}/export?format={pdf|docx|md}
```

---

## 2. Claude-like Artifacts System

### Concept

"Artifacts" are standalone content pieces (code, documents, diagrams) that:

1. Are **separated** from the chat stream.
2. Render in a **side panel** (usually right side).
3. Are **interactive** (e.g., React components, previews).

### Implementation Plan

#### A. Backend (LLM & Prompting)

The LLM must be "taught" to wrap artifact content in XML tags.
**System Prompt Addition**:

```text
When generating standalone content like code, documents, or diagrams, wrap them in:
<antArtifact identifier="unique-id" type="application/vnd.ant.code" language="python" title="File Name">
... content ...
</antArtifact>
```

#### B. Frontend (Architecture)

We need to capture these tags *during the stream* and divert the content.

**Components**:

1. **`ArtifactContext`**: Global state to hold the "Current Active Artifact".
2. **`MessageParser`**:
    - Instead of just `react-markdown`, we need a pre-processor.
    - **Logic**: Use Regex or a streaming parser to detect `<antArtifact>`.
    - **Action**:
        - Hide the `<antArtifact>...</antArtifact>` block from the main chat bubble.
        - Render a button: `[View Artifact: Title]`.
        - Update `ArtifactContext` with the content.
3. **`ArtifactPanel`**:
    - A new resizable panel on the right side of `ChatPane`.
    - Renders content based on `type`:
        - `code`: Syntax highlighter (Prism/Shiki).
        - `markdown`: Rendered markdown.
        - `react`: `sandpack` or `iframe` for live preview (advanced).

#### C. Data Structure (Frontend State)

```typescript
interface Artifact {
  id: string;
  type: 'code' | 'markdown' | 'html';
  title: string;
  content: string;
  language?: string;
}
```

---

## 3. Implementation Roadmap

### Phase 1: Chat Export

1. Add `weasyprint` and `markdown` to `backend/requirements.txt`.
2. Create `core/export.py` service.
3. Add endpoint in `api/routes/threads.py`.
4. Add "Export" button in Frontend Header.

### Phase 2: Artifacts Core

1. Update `core/prompts.py` (or similar) with Artifact XML instructions.
2. Create `ArtifactContext` in Frontend.
3. Create `ArtifactPanel` UI (Right sidebar).

### Phase 3: Artifact Parsing

1. Implement `useArtifactParser` hook to extract tags from message stream.
2. Replace `<antArtifact>` in chat with specific UI Card.
