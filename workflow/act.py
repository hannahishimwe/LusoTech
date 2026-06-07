from config import get_supabase_config

supabase = get_supabase_config()

SUPABASE_HEADERS = f'{{"apikey": "{supabase.key}", "Authorization": "Bearer {supabase.key}", "Content-Type": "application/json", "Prefer": "return=representation"}}'


def build_summary_node(workflow_def):
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="You are a supplier quality reporting assistant. Output only plain text. No markdown, no JSON.",
        template="""Write a concise 4-6 line lot summary for internal notification.

Extracted CoA data:
((extracted_json))

Verdict: ((category))
Rationale: ((reasoning))

Include: supplier name, PO reference, material grade, heat number, verdict, and one sentence rationale.""",
        model=["claude-4.5-sonnet"],
        temperature=0.0,
        max_tokens=300,
        inputs={"variables": {"keys": ["extracted_json", "category", "reasoning"]}},
    )


def build_lot_insert_node(workflow_def, status: str):
    erp_posted = "true" if status == "released" else "false"
    po_blocked = "false" if status == "released" else "true"

    return workflow_def.node("APIRequestV2Node").config(
        request_method="POST",
        url=f"{supabase.url}/functions/v1/insert-lot",
        headers='{"Content-Type": "application/json"}',
        body=f'{{"extracted_json": ((extracted_json)), "category": "((category))", "reasoning": "((reasoning))", "status": "{status}", "erp_receipt_posted": {erp_posted}, "po_acceptance_blocked": {po_blocked}}}',
        parse_json=True,
        on_error_behavior="skip",
        has_on_error_output=True,
        inputs={"inputs": {"keys": ["extracted_json", "category", "reasoning"]}},
    )


def build_ncr_draft_node(workflow_def):
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="You are a supplier quality engineer. Output only plain text. No markdown.",
        template="""Draft a Non-Conformance Report for the following failed lot.

Extracted CoA data:
((extracted_json))

Fail rationale: ((reasoning))

Include: NCR header, supplier details, material details, list of failed checks citing the spec rule, recommended disposition (quarantine), and signature block for SQE review.""",
        model=["claude-4.5-sonnet"],
        temperature=0.0,
        max_tokens=1000,
        inputs={"variables": {"keys": ["extracted_json", "reasoning", "category"]}},
    )


def build_pass_email_node(workflow_def):
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="You are a supplier quality notification system. Output only the email, no commentary.",
        template="""Write a release notification email for the warehouse team.

Extract the coil_lot_id from this JSON and use it in the subject line:
((extracted_json))

Subject line format: [PASS] Lot <coil_lot_id> — released for use

Verdict: ((category))

Summary:
((summary))

Output format:
Subject: <subject line>

<email body>""",
        model=["claude-4.5-sonnet"],
        temperature=0.0,
        max_tokens=400,
        inputs={"variables": {"keys": ["extracted_json", "summary"]}},
    )


def build_hold_email_node(workflow_def):
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="You are a supplier quality notification system. Output only the email, no commentary.",
        template="""Write a hold notification email for the SQE team requesting human review.

Extract the coil_lot_id from this JSON and use it in the subject line:
((extracted_json))

Subject line format: [CONDITIONAL] Lot <coil_lot_id> — review required

Verdict: ((category))

Summary:
((summary))

The reviewer must decide to APPROVE or REJECT this lot. Make this clear in the email body.

Output format:
Subject: <subject line>

<email body>""",
        model=["claude-4.5-sonnet"],
        temperature=0.0,
        max_tokens=400,
        inputs={"variables": {"keys": ["extracted_json", "summary"]}},
    )


def build_fail_email_node(workflow_def):
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="You are a supplier quality notification system. Output only the email, no commentary.",
        template="""Write a failure notification email for the SQE team.

Extract the coil_lot_id from this JSON and use it in the subject line:
((extracted_json))

Subject line format: [FAIL] Lot <coil_lot_id> — quarantined, NCR drafted

Verdict: ((category))

Summary:
((summary))

NCR Draft:
((ncr_draft))

Output format:
Subject: <subject line>

<email body including full NCR draft>""",
        model=["claude-4.5-sonnet"],
        temperature=0.0,
        max_tokens=800,
        inputs={"variables": {"keys": ["extracted_json", "summary", "ncr_draft"]}},
    )