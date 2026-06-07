from pathlib import Path


def load_prompt(filename: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / filename
    with open(prompt_path, "r") as f:
        return f.read()


def build_router_node(workflow_def):
    prompt = load_prompt("router.txt")

    router = workflow_def.node("EnsembleCategorizerNode").config(
        system_prompt="""You are a strict supplier quality decision engine.

You evaluate DC04 steel CoA extraction data against specification LSQ-SPEC-DC04-r3.

You must produce a structured decision with full audit information.""",

        template=f"""{prompt}

Extracted CoA JSON:
((input))""",
        categories=[
    {"Category": "PASS", "Description": """Take this route if and only if ALL of the following are true simultaneously:
1. All eight mandatory fields are present and non-null: supplier_name, po_reference, heat_number, coil_lot_id, material_grade, manufacturing_date, certificate_type, inspector_signature.
2. All chemical composition values are within their maximum limits: carbon_c_pct ≤ 0.080, manganese_mn_pct ≤ 0.400, phosphorus_p_pct ≤ 0.030, sulphur_s_pct ≤ 0.030, titanium_ti_pct ≤ 0.300.
3. All mechanical properties are within their limits: yield_strength_re_mpa ≥ 140 AND ≤ 210, tensile_strength_rm_mpa ≥ 270 AND ≤ 350, elongation_a80_pct ≥ 38, plastic_strain_ratio_r90 ≥ 1.6, strain_hardening_exp_n90 ≥ 0.18, hardness_hrb ≤ 60.
4. No chemical or mechanical field is null. A null value cannot satisfy a PASS."""},

    {"Category": "CONDITIONAL", "Description": """Take this route if and only if ALL of the following are true simultaneously:
1. All eight mandatory fields are present and non-null: supplier_name, po_reference, heat_number, coil_lot_id, material_grade, manufacturing_date, certificate_type, inspector_signature.
2. All critical chemical elements are within limits: carbon_c_pct ≤ 0.080, phosphorus_p_pct ≤ 0.030, sulphur_s_pct ≤ 0.030.
3. All critical mechanical properties are within limits: yield_strength_re_mpa ≥ 140 AND ≤ 210, tensile_strength_rm_mpa ≥ 270 AND ≤ 350.
4. Exactly one non-critical property is out of tolerance and its deviation is ≤ 2%: manganese_mn_pct max 0.400, titanium_ti_pct max 0.300, elongation_a80_pct min 38, plastic_strain_ratio_r90 min 1.6, strain_hardening_exp_n90 min 0.18, hardness_hrb max 60.
5. No mandatory or critical field is null."""},

    {"Category": "FAIL", "Description": """Take this route if ANY of the following are true:
1. One or more mandatory fields are null or missing: supplier_name, po_reference, heat_number, coil_lot_id, material_grade, manufacturing_date, certificate_type, inspector_signature.
2. Any critical chemical element exceeds its maximum: carbon_c_pct > 0.080, phosphorus_p_pct > 0.030, sulphur_s_pct > 0.030.
3. Any critical mechanical property is outside its limits: yield_strength_re_mpa < 140 OR > 210, tensile_strength_rm_mpa < 270 OR > 350.
4. Any non-critical property deviates from its limit by more than 2%.
5. More than one non-critical property is out of tolerance regardless of deviation magnitude.
6. Any critical or mandatory field is null."""}
],

        temperature=0.0,
    )

    return router

def build_category_router_node(workflow_def):
    check_pass = workflow_def.node("ComplexConditionalNode").config(
        conditions=[{
            "logic": "OR",
            "condition_type": "REGULAR",
            "regular_condition": {
                "field_type": "TEXT",
                "field": "((category))",
                "condition": "CONTAINS",
                "text_value": "PASS",
                "number_value": 0
            }
        }],
        output_true="((category))",
        output_false="((category))",
        inputs={"variables": {"keys": ["category"]}},
    )

    check_conditional = workflow_def.node("ComplexConditionalNode").config(
        conditions=[{
            "logic": "OR",
            "condition_type": "REGULAR",
            "regular_condition": {
                "field_type": "TEXT",
                "field": "((category))",
                "condition": "CONTAINS",
                "text_value": "CONDITIONAL",
                "number_value": 0
            }
        }],
        output_true="((category))",
        output_false="((category))",
        inputs={"variables": {"keys": ["category"]}},
    )

    workflow_def.link(
        check_pass.output("when_false"),
        check_conditional.input("variables", key="category"),
    )

    return check_pass, check_conditional



def build_verdict_node(workflow_def, verdict: str):
    prompt = load_prompt(f"{verdict.lower()}.txt")  # pass.txt, conditional.txt, fail.txt
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="""You are a strict supplier quality decision engine.
You evaluate DC04 steel CoA extraction data against specification LSQ-SPEC-DC04-r3.
Output only valid JSON. Never add commentary outside the JSON object.""",
        template=f"""{prompt}

Extracted CoA JSON:
((extracted_json))""",
        model=["claude-4.5-sonnet"],
        temperature=0.0,
        max_tokens=1000,
        inputs={"variables": {"keys": ["extracted_json"]}},
    )