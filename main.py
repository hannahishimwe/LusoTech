
import argparse
from noxus_sdk.client import Client
from noxus_sdk.workflows import WorkflowDefinition
from workflow.extract import build_extraction_node, build_extraction_passthrough_node
from workflow.decide import build_router_node, build_category_router_node
from workflow.act import (
    build_summary_node,
    build_lot_insert_node,
    build_ncr_draft_node,
    build_pass_email_node,
    build_hold_email_node,
    build_fail_email_node,
)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()
    client = Client(api_key=args.api_key)

    wf = WorkflowDefinition(name="SQE Pipeline")

    # =====================
    # CORE NODES
    # =====================
    extraction   = build_extraction_node(wf)
    passthrough  = build_extraction_passthrough_node(wf)
    router       = build_router_node(wf)
    check_pass, check_conditional = build_category_router_node(wf)

    # =====================
    # SHARED — runs once before branching
    # =====================
    summary = build_summary_node(wf)

    # =====================
    # PASS NODES
    # =====================
    pass_lot_insert = build_lot_insert_node(wf, status="released")
    pass_email      = build_pass_email_node(wf)
    output_pass     = wf.node("OutputNode")

    # =====================
    # CONDITIONAL NODES
    # =====================
    cond_lot_insert = build_lot_insert_node(wf, status="held")
    hold_email      = build_hold_email_node(wf)
    output_cond     = wf.node("OutputNode")

    # =====================
    # FAIL NODES
    # =====================
    fail_lot_insert = build_lot_insert_node(wf, status="quarantined")
    ncr_draft       = build_ncr_draft_node(wf)
    fail_email      = build_fail_email_node(wf)
    output_fail     = wf.node("OutputNode")

    # =====================
    # WIRES — core
    # =====================
    wf.link(extraction.output("text_output"), passthrough.input("variables", key="extracted_json"))
    wf.link(extraction.output("text_output"), router.input("input"))
    wf.link(router.output("category"),        check_pass.input("variables", key="category"))

    # =====================
    # WIRES — summary
    # =====================
    wf.link(passthrough.output("text_output"), summary.input("variables", key="extracted_json"))
    wf.link(router.output("category"),         summary.input("variables", key="category"))
    wf.link(router.output("reasoning"),        summary.input("variables", key="reasoning"))

    # =====================
    # WIRES — PASS
    # =====================

    wf.link(passthrough.output("text_output"), pass_lot_insert.input("inputs", key="extracted_json"))
    wf.link(check_pass.output("when_true"),    pass_lot_insert.input("inputs", key="category"))
    wf.link(router.output("reasoning"),        pass_lot_insert.input("inputs", key="reasoning"))

    wf.link(check_pass.output("when_true"),     pass_email.input("variables", key="category"))
    wf.link(summary.output("text_output"),      pass_email.input("variables", key="summary"))
    wf.link(passthrough.output("text_output"),  pass_email.input("variables", key="extracted_json"))

    wf.link(pass_email.output("text_output"),   output_pass.input())

    # check_pass false → check_conditional
    wf.link(check_pass.output("when_false"),   check_conditional.input("variables", key="category"))

    # =====================
    # WIRES — CONDITIONAL
    # =====================
    wf.link(passthrough.output("text_output"),     cond_lot_insert.input("inputs", key="extracted_json"))
    wf.link(check_conditional.output("when_true"), cond_lot_insert.input("inputs", key="category"))
    wf.link(router.output("reasoning"),            cond_lot_insert.input("inputs", key="reasoning"))

    wf.link(check_conditional.output("when_true"),  hold_email.input("variables", key="category")) 
    wf.link(summary.output("text_output"),      hold_email.input("variables", key="summary"))
    wf.link(passthrough.output("text_output"),  hold_email.input("variables", key="extracted_json"))
    wf.link(hold_email.output("text_output"),   output_cond.input())

    # =====================
    # WIRES — FAIL
    # =====================
    wf.link(passthrough.output("text_output"),     fail_lot_insert.input("inputs", key="extracted_json"))
    wf.link(check_conditional.output("when_false"), fail_lot_insert.input("inputs", key="category"))
    wf.link(router.output("reasoning"),             fail_lot_insert.input("inputs", key="reasoning"))

    wf.link(passthrough.output("text_output"),      ncr_draft.input("variables", key="extracted_json"))
    wf.link(router.output("reasoning"),             ncr_draft.input("variables", key="reasoning"))
    wf.link(check_conditional.output("when_false"), ncr_draft.input("variables", key="category"))

    wf.link(check_conditional.output("when_false"), fail_email.input("variables", key="category"))
    wf.link(summary.output("text_output"),      fail_email.input("variables", key="summary"))
    wf.link(passthrough.output("text_output"),  fail_email.input("variables", key="extracted_json"))
    wf.link(ncr_draft.output("text_output"),    fail_email.input("variables", key="ncr_draft"))

    wf.link(fail_email.output("text_output"),   output_fail.input())


    # =====================
    # SAVE
    # =====================
    saved = client.workflows.save(wf)
    print("Created workflow:", saved.id)
    


if __name__ == "__main__":
    main()