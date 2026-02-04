"""
Testes básicos das ferramentas do Módulo 1C.

Como o pytest funciona (resumo rápido):
- Ele descobre automaticamente funções cujo nome começa com `test_`.
- "Fixtures" (como `unique_email`) são passadas como argumentos e preparadas antes do teste.
- Usamos `assert` para verificar resultados esperados — se falhar, o pytest mostra o erro.

Por que usamos `.invoke({...})` nas ferramentas:
- As funções decoradas com `@tool` viram `StructuredTool` (LangChain). A forma recomendada de chamá-las é
  `tool.invoke({"arg": valor, ...})` — a chamada direta `tool(...)` é deprecada.
- `.invoke` recebe um dicionário com os parâmetros esperados (mesmos nomes dos argumentos da função).

UUID → string nos argumentos:
- Em alguns tools, o `args_schema` (Pydantic) espera `str`. Quando o banco retorna um UUID como objeto,
  convertemos com `str(uuid)` ao passar para `.invoke`.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent import tools as t


def test_list_lead_status(db_ready):
    r = t.list_lead_status.invoke({})
    assert r.get("error") is None
    items = r["data"]["items"]
    assert len(items) >= 6
    assert any(x["codigo"] == "novo" for x in items)


def test_create_and_get_lead(unique_email):
    # Cria um lead novo usando um e-mail único (evita duplicidade)
    r = t.create_lead.invoke({"nome": "João Teste", "email": unique_email, "empresa": "ACME"})
    assert r.get("error") is None
    lead_id = r["data"]["lead_id"]
    assert lead_id and len(str(lead_id)) == 36

    # Recupera o mesmo lead usando a referência natural (email)
    r2 = t.get_lead.invoke({"ref": unique_email})
    assert r2.get("error") is None
    assert r2["data"]["lead_id"] == lead_id
    print(f"[create_lead] {r['message']} id={lead_id} email={unique_email}")
    print(f"[get_lead] {r2['message']} nome={r2['data']['nome']} status={r2['data']['status_codigo']}")


def test_notes_for_lead(unique_email):
    lead = t.create_lead.invoke({"nome": "Maria Teste", "email": unique_email, "empresa": "Beta"})
    lead_id = lead["data"]["lead_id"]

    n1 = t.add_note_to_lead.invoke({"lead_ref_ou_id": str(lead_id), "texto": "Retornar orçamento amanhã"})
    assert n1.get("error") is None
    assert n1["data"]["note_id"]

    lst = t.list_notes.invoke({"lead_ref_ou_id": str(lead_id)})
    assert lst.get("error") is None
    assert lst["data"]["total"] >= 1
    assert any(item["note_id"] == n1["data"]["note_id"] for item in lst["data"]["items"])
    print(f"[add_note_to_lead] note_id={n1['data']['note_id']}")
    print(f"[list_notes] total={lst['data']['total']}")


def test_tasks_create_and_complete(unique_email):
    lead = t.create_lead.invoke({"nome": "Carlos Teste", "email": unique_email, "empresa": "Gamma"})
    lead_id = lead["data"]["lead_id"]

    tk = t.create_task.invoke({"lead_ref_ou_id": str(lead_id), "titulo": "Ligar amanhã", "tipo": "ligacao"})
    assert tk.get("error") is None
    tarefa_id = tk["data"]["tarefa_id"]

    done = t.complete_task.invoke({"tarefa_id": str(tarefa_id)})
    assert done.get("error") is None
    assert done["data"]["status"] == "concluida"

    lst = t.list_tasks.invoke({"lead_ref_ou_id": str(lead_id), "status": "concluida"})
    assert lst.get("error") is None
    assert any(item["tarefa_id"] == tarefa_id for item in lst["data"]["items"]) 
    print(f"[create_task] tarefa_id={tarefa_id}")
    print(f"[complete_task] status={done['data']['status']}")
    print(f"[list_tasks] total={lst['data']['total']}")


def test_proposal_draft_items_totals_export(unique_email):
    lead = t.create_lead.invoke({"nome": "Ana Teste", "email": unique_email, "empresa": "Delta"})
    lead_id = lead["data"]["lead_id"]

    prop = t.draft_proposal.invoke({"lead_ref_ou_id": str(lead_id), "titulo": "Proposta Delta"})
    assert prop.get("error") is None
    proposta_id = prop["data"]["proposta_id"]

    item = t.add_proposal_item.invoke({"proposta_id": str(proposta_id), "descricao": "Consultoria", "quantidade": 2, "preco_unitario": 5000})
    assert item.get("error") is None

    tot = t.calculate_proposal_totals.invoke({"proposta_id": str(proposta_id)})
    assert tot.get("error") is None
    assert tot["data"]["subtotal"] >= 10000
    assert tot["data"]["total"] == tot["data"]["subtotal"]

    md = t.export_proposal.invoke({"proposta_id": str(proposta_id), "formato": "markdown"})
    assert md.get("error") is None
    assert "Proposta exportada" in md["message"]
    assert "markdown" == md["data"]["formato"]
    print(f"[draft_proposal] proposta_id={proposta_id}")
    print(f"[add_proposal_item] item_id={item['data']['item_id']}")
    print(f"[calculate_proposal_totals] subtotal={tot['data']['subtotal']} total={tot['data']['total']}")
    print(f"[export_proposal] formato={md['data']['formato']} len={len(md['data']['conteudo'])}")


def test_leads_search_list_and_update(unique_email):
    t.create_lead.invoke({"nome": "Alice ACME", "email": unique_email, "empresa": "ACME"})
    t.create_lead.invoke({"nome": "Bob Beta", "empresa": "Beta"})

    res = t.search_leads.invoke({"consulta": "acm"})
    assert res.get("error") is None
    assert res["data"]["total"] >= 1

    lst = t.list_leads.invoke({})
    assert lst.get("error") is None
    assert lst["data"]["total"] >= 2

    lead_id = t.get_lead.invoke({"ref": unique_email})["data"]["lead_id"]
    up = t.update_lead.invoke({"lead_id": str(lead_id), "status_codigo": "qualificado", "qualificado": True})
    assert up.get("error") is None
    got = t.get_lead.invoke({"ref": unique_email})
    assert got["data"]["status_codigo"] == "qualificado"


def test_leads_resolve_and_respond(unique_email):
    t.create_lead.invoke({"nome": "Resolver Teste", "email": unique_email})
    r = t.resolve_lead.invoke({"ref": unique_email})
    assert r.get("error") is None
    assert r["data"]["lead_id"]

    resp = t.respond_message.invoke({"mensagem": "ok", "intent": "conversa_geral"})
    assert resp["message"] == "ok"
    assert resp["intent"] == "conversa_geral"
