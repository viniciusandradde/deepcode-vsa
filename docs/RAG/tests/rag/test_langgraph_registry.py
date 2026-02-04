from pathlib import Path
import json


def test_graphs_registered():
    p = Path("langgraph.json")
    assert p.exists(), "langgraph.json não encontrado"
    data = json.loads(p.read_text(encoding="utf-8"))
    graphs = data.get("graphs") or {}
    # Grafos existentes + novos do M2
    assert "workflow" in graphs
    assert "proposal_agent_v2" in graphs
    assert "rag_ingest" in graphs

