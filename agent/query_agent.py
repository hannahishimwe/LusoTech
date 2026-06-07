"""
agent.py
Builds and saves the Lusotech SQE Query Agent on the Noxus platform.
"""

from noxus_sdk.client import Client
from noxus_sdk.resources import AgentSettings
from noxus_sdk.resources.conversations import WorkflowTool
from noxus_sdk.workflows import WorkflowDefinition
from config import get_noxus_config, get_supabase_config

AGENT_NAME = "Lusotech SQE Data Agent"
QUERY_WORKFLOW_NAME = "Lusotech SQE — Data Query Workflow v3"

supabase = get_supabase_config()

SUPABASE_HEADERS = f'apikey: {supabase.key}\nAuthorization: Bearer {supabase.key}'

AGENT_SYSTEM_PROMPT = """You are the Lusotech SQE Data Assistant — a specialist \
analytics agent for the Supplier Quality Engineering team.

SCOPE
-----
You answer questions ONLY about data that exists in the Lusotech SQE database:
  • Lots (coil_lot_id, supplier, material grade, status, chemical analysis, mechanical results, dates)
  • NCR drafts (ncr_id, lot_id, fail_reasons, status, assigned_to)
  • Supplier registry (name, is_approved)

If a question falls outside this scope, or if the data query returns no rows,
say so clearly — do NOT invent or estimate figures.

BEHAVIOUR
---------
1. When the user asks a data question, call the "SQE Data Query" workflow tool.
2. When calling the tool, pass ONLY the path and query string — never the base URL.

   Available tables and columns:
     lots       — id, coil_lot_id, cert_number, po_reference, supplier_id, supplier_name,
                  heat_number, material_grade, manufacturing_date, certificate_type,
                  inspector_signature, carbon_c_pct, manganese_mn_pct, phosphorus_p_pct,
                  sulphur_s_pct, titanium_ti_pct, yield_strength_re_mpa, tensile_strength_rm_mpa,
                  elongation_a80_pct, plastic_strain_ratio_r90, strain_hardening_exp_n90,
                  hardness_hrb, thickness_mm, width_mm, flatness_iu, coil_mass_kg,
                  verdict, verdict_reasoning, failed_checks, status, status_updated_at,
                  status_updated_by, status_reason, erp_receipt_posted, erp_posted_at,
                  po_acceptance_blocked, ncr_id, created_at

     ncr_drafts — id, lot_id, supplier_id, fail_reasons, status, assigned_to,
                  resolution, resolution_notes, closed_at, closed_by, created_at, updated_at

     suppliers  — id, name, plant_address, phone, email, vat_number, iso_9001,
                  iatf_16949, is_approved, approved_at, approved_by, created_at

   Format: table?select=col1,col2&filter=eq.value&order=col.desc&limit=50

   Examples:
     lots?select=coil_lot_id,supplier_name,verdict,status&limit=50
     lots?select=coil_lot_id,verdict,failed_checks&verdict=eq.FAIL&order=created_at.desc&limit=50
     lots?select=coil_lot_id,status&status=eq.quarantined&order=created_at.desc&limit=50
     ncr_drafts?select=id,lot_id,fail_reasons,status,resolution&status=eq.draft&limit=50
     suppliers?select=id,name,is_approved&is_approved=eq.true

3. Interpret the returned JSON and answer in plain language.
4. When the user asks for a chart, table, or visual breakdown, produce one.
   Prefer bar charts for counts, tables for detail, trend lines for volume.
5. Always cite the underlying data (row counts, date range) so the user can verify.
6. Never answer questions about production scheduling, ERP transactions,
   logistics, or anything not in the SQE database.
7. If the tool returns an empty array [], tell the user no records matched.
8. If the tool returns an error object, report it and suggest refining the query.
"""


def build_query_workflow(client: Client) -> object:
    wf = WorkflowDefinition(name=QUERY_WORKFLOW_NAME)

    input_node = wf.node("InputNode")

    api_node = wf.node("APIRequestV2Node").config(
        request_method="GET",
        url=f"{supabase.url}/rest/v1/((input))",
        headers=SUPABASE_HEADERS,
        parse_json=True,
    )

    output_node = wf.node("OutputNode")

    wf.link(input_node.output(), api_node.input("inputs", key="input"))
    wf.link(api_node.output("body"), output_node.input())

    saved = client.workflows.save(wf)
    print(f"Query workflow saved: {saved.id}")
    return saved


def build_agent(client: Client) -> object:
    query_workflow = _get_or_create_query_workflow(client)

    workflow_tool = WorkflowTool(
        workflow_id=query_workflow.id,
        enabled=True,
        extra_instructions=(
            "Call this tool for any question about lots, NCRs, or suppliers. "
            "Pass ONLY the path and query string, e.g.: "
            "lots?select=coil_lot_id,status&status=eq.quarantined&limit=50"
        ),
    )

    agent_settings = AgentSettings(
        model=["claude-4.5-sonnet"],
        temperature=0.2,
        max_tokens=2000,
        tools=[workflow_tool],
        extra_instructions=AGENT_SYSTEM_PROMPT,
    )

    existing = _find_agent_by_name(client, AGENT_NAME)
    if existing:
        updated = client.agents.update(
            agent_id=existing.id,
            name=AGENT_NAME,
            settings=agent_settings,
        )
        print(f"Agent updated: {updated.id}")
        return updated

    agent = client.agents.create(name=AGENT_NAME, settings=agent_settings)
    print(f"Agent created: {agent.id}")
    return agent


def _get_or_create_query_workflow(client: Client) -> object:
    # Always delete and recreate to pick up latest changes
    for wf in client.workflows.list():
        if wf.name == QUERY_WORKFLOW_NAME:
            print(f"Deleting old workflow: {wf.id}")
            try:
                client.workflows.delete(wf.id)
            except Exception:
                pass
            break
    return build_query_workflow(client)


def _find_agent_by_name(client: Client, name: str):
    for agent in client.agents.list():
        if agent.name == name:
            return agent
    return None


if __name__ == "__main__":
    client = Client(api_key=get_noxus_config().api_key)
    agent = build_agent(client)
    print(f"Done. Agent ID: {agent.id}")