from pathlib import Path
from config import get_supabase_config

supabase = get_supabase_config()

SUPABASE_HEADERS = {
    "apikey": supabase.key,
    "Authorization": f"Bearer {supabase.key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# =====================
# SUPPLIER LOOKUP
# =====================

def build_supplier_lookup_node(workflow_def):
    """
    Looks up supplier by name before any insert.
    Returns supplier id and is_approved flag.
    If supplier not found or not approved, pipeline short circuits.
    """
    return workflow_def.node("APICallNode").config(
        url=f"{supabase.url}/rest/v1/suppliers?name=eq.((supplier_name))&select=id,is_approved",
        method="GET",
        headers=SUPABASE_HEADERS,
        timeout_seconds=30,
        retry_attempts=3,
        retry_delay=1
    )


def build_supplier_approval_check_node(workflow_def):
    """
    Checks if supplier is approved before running extraction.
    Short circuits pipeline if not approved.
    """
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="""You are a supplier quality gate checker. 
        You output only valid JSON. Never add commentary outside the JSON object.""",
        template="""Examine this supplier lookup result: ((supplier_lookup_result))

        Check the following:
        1. Did the lookup return a result? If the array is empty the supplier 
           does not exist in our system.
        2. Is is_approved set to true?

        Output only the following JSON:
        {
            "approved": true | false,
            "supplier_id": "uuid or null if not found",
            "reason": "plain English explanation"
        }""",
        model=["claude-sonnet-4-20250514"],
        temperature=0.0,
        max_tokens=200
    )


# =====================
# SUPABASE HELPERS
# =====================

def build_lot_insert_node(workflow_def, status: str):
    """
    Inserts a new lot row into Supabase.
    Status is passed in depending on verdict path.
    supplier_id comes from the supplier lookup node.
    """
    erp_posted = "true" if status == "released" else "false"
    po_blocked = "false" if status == "released" else "true"
    erp_posted_at = '"((erp_posted_at))"' if status == "released" else "null"

    return workflow_def.node("APICallNode").config(
        url=f"{supabase.url}/rest/v1/lots",
        method="POST",
        headers=SUPABASE_HEADERS,
        body_template=f'''{{
            "coil_lot_id":               "((coil_lot_id))",
            "cert_number":               "((cert_number))",
            "po_reference":              "((po_reference))",
            "supplier_id":               "((supplier_id))",
            "heat_number":               "((heat_number))",
            "material_grade":            "((material_grade))",
            "manufacturing_date":        "((manufacturing_date))",
            "certificate_type":          "((certificate_type))",
            "inspector_signature":       "((inspector_signature))",
            "carbon_c_pct":              ((carbon_c_pct)),
            "manganese_mn_pct":          ((manganese_mn_pct)),
            "phosphorus_p_pct":          ((phosphorus_p_pct)),
            "sulphur_s_pct":             ((sulphur_s_pct)),
            "titanium_ti_pct":           ((titanium_ti_pct)),
            "yield_strength_re_mpa":     ((yield_strength_re_mpa)),
            "tensile_strength_rm_mpa":   ((tensile_strength_rm_mpa)),
            "elongation_a80_pct":        ((elongation_a80_pct)),
            "plastic_strain_ratio_r90":  ((plastic_strain_ratio_r90)),
            "strain_hardening_exp_n90":  ((strain_hardening_exp_n90)),
            "hardness_hrb":              ((hardness_hrb)),
            "thickness_mm":              ((thickness_mm)),
            "width_mm":                  ((width_mm)),
            "flatness_iu":               ((flatness_iu)),
            "coil_mass_kg":              ((coil_mass_kg)),
            "status":                    "{status}",
            "status_updated_by":         "system",
            "status_reason":             "((rationale))",
            "failed_checks":             ((failed_checks)),
            "erp_receipt_posted":        {erp_posted},
            "erp_posted_at":             {erp_posted_at},
            "po_acceptance_blocked":     {po_blocked}
        }}''',
        timeout_seconds=30,
        retry_attempts=3,
        retry_delay=1
    )


def build_ncr_insert_node(workflow_def):
    """
    Inserts a new NCR draft row into Supabase.
    Only called on FAIL path.
    Returns NCR id to be linked back to lot.
    """
    return workflow_def.node("APICallNode").config(
        url=f"{supabase.url}/rest/v1/ncr_drafts",
        method="POST",
        headers=SUPABASE_HEADERS,
        body_template='''{
            "lot_id":        "((lot_id))",
            "supplier_id":   "((supplier_id))",
            "fail_reasons":  ((fail_reasons)),
            "status":        "draft",
            "assigned_to":   "SQE"
        }''',
        timeout_seconds=30,
        retry_attempts=3,
        retry_delay=1
    )


def build_lot_update_ncr_node(workflow_def):
    """
    Updates the lot row with the NCR id after NCR is created.
    Only called on FAIL path after ncr_insert.
    """
    return workflow_def.node("APICallNode").config(
        url=f"{supabase.url}/rest/v1/lots?coil_lot_id=eq.((coil_lot_id))",
        method="PATCH",
        headers=SUPABASE_HEADERS,
        body_template='''{
            "ncr_id": "((ncr_id))"
        }''',
        timeout_seconds=30,
        retry_attempts=3,
        retry_delay=1
    )


# =====================
# EMAIL NODES
# =====================

def build_warehouse_email_node(workflow_def):
    """
    Notifies warehouse on PASS.
    Sends lot summary.
    """
    return workflow_def.node("EmailNode").config(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="{{EMAIL_USERNAME}}",
        password="{{EMAIL_PASSWORD}}",
        to_addresses=["warehouse@lusotech.pt"],
        subject_template="[RELEASED] Lot ((coil_lot_id)) — cleared for use",
        body_template="""Hello Warehouse team,

Lot ((coil_lot_id)) has passed supplier quality inspection and has been
released for use.

Summary:
- Supplier:           ((supplier_name))
- PO Reference:       ((po_reference))
- Material Grade:     ((material_grade))
- Heat Number:        ((heat_number))
- Manufacturing Date: ((manufacturing_date))
- Coil Mass:          ((coil_mass_kg)) kg
- Thickness:          ((thickness_mm)) mm
- Width:              ((width_mm)) mm

Verdict rationale:
((rationale))

The lot has been written to ERP and is available for production.

Lusotech SQE System
""",
        html_format=False
    )


def build_sqe_hold_email_node(workflow_def):
    """
    Notifies SQE on CONDITIONAL.
    Includes deviation detail for engineering review.
    """
    return workflow_def.node("EmailNode").config(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="{{EMAIL_USERNAME}}",
        password="{{EMAIL_PASSWORD}}",
        to_addresses=["sqe-inbox@lusotech.pt"],
        subject_template="[HOLD] Lot ((coil_lot_id)) — minor deviation, review required",
        body_template="""Hello SQE team,

Lot ((coil_lot_id)) has been placed on HOLD pending your engineering review.

Summary:
- Supplier:       ((supplier_name))
- PO Reference:   ((po_reference))
- Material Grade: ((material_grade))
- Heat Number:    ((heat_number))

Verdict rationale:
((rationale))

Deviation detail:
((non_critical_deviation))

Please review and update the lot status to released or quarantined.

Lusotech SQE System
""",
        html_format=False
    )


def build_sqe_fail_email_node(workflow_def):
    """
    Notifies SQE on FAIL.
    Includes all failed checks and NCR reference.
    """
    return workflow_def.node("EmailNode").config(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="{{EMAIL_USERNAME}}",
        password="{{EMAIL_PASSWORD}}",
        to_addresses=["sqe-inbox@lusotech.pt"],
        subject_template="[FAIL] Lot ((coil_lot_id)) — quarantined, NCR drafted",
        body_template="""Hello SQE team,

Lot ((coil_lot_id)) has FAILED supplier quality inspection and has been
quarantined. An NCR has been automatically drafted.

Summary:
- Supplier:       ((supplier_name))
- PO Reference:   ((po_reference))
- Material Grade: ((material_grade))
- Heat Number:    ((heat_number))

Verdict rationale:
((rationale))

Failed checks:
((failed_checks))

Actions taken:
- Lot status set to: quarantined
- PO acceptance blocked
- NCR drafted and assigned to SQE
- NCR reference: ((ncr_id))

Please review the NCR and action accordingly.

Lusotech SQE System
""",
        html_format=False
    )


# =====================
# ACTION BUNDLES
# =====================

def build_pass_actions(workflow_def):
    supplier_lookup = build_supplier_lookup_node(workflow_def)
    approval_check = build_supplier_approval_check_node(workflow_def)
    lot_insert = build_lot_insert_node(workflow_def, status="released")
    warehouse_email = build_warehouse_email_node(workflow_def)
    return supplier_lookup, approval_check, lot_insert, warehouse_email


def build_conditional_actions(workflow_def):
    supplier_lookup = build_supplier_lookup_node(workflow_def)
    approval_check = build_supplier_approval_check_node(workflow_def)
    lot_insert = build_lot_insert_node(workflow_def, status="held")
    sqe_email = build_sqe_hold_email_node(workflow_def)
    return supplier_lookup, approval_check, lot_insert, sqe_email


def build_fail_actions(workflow_def):
    supplier_lookup = build_supplier_lookup_node(workflow_def)
    approval_check = build_supplier_approval_check_node(workflow_def)
    lot_insert = build_lot_insert_node(workflow_def, status="quarantined")
    ncr_insert = build_ncr_insert_node(workflow_def)
    lot_update_ncr = build_lot_update_ncr_node(workflow_def)
    sqe_email = build_sqe_fail_email_node(workflow_def)
    return supplier_lookup, approval_check, lot_insert, ncr_insert, lot_update_ncr, sqe_email