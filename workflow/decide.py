from pathlib import Path

def load_prompt(filename: str) -> str:
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / filename
    with open(prompt_path, "r") as f:
        return f.read()

def build_pass_node(workflow_def):
    prompt = load_prompt("check_pass.txt")

    pass_node = workflow_def.node("TextGenerationNode").config(
        system_prompt="""You are a supplier quality inspector for Lusotech 
        Industries evaluating DC04 cold-rolled steel against specification 
        LSQ-SPEC-DC04-r3. You output only valid JSON. Never add commentary 
        outside the JSON object.""",
        template=f"""{prompt}

((extracted_json))""",
        model=["claude-sonnet-4-20250514"],
        temperature=0.0,
        max_tokens=1000,
    )

    return pass_node


def build_conditional_node(workflow_def):
    prompt = load_prompt("check_conditional.txt")

    conditional_node = workflow_def.node("TextGenerationNode").config(
        system_prompt="""You are a supplier quality inspector for Lusotech 
        Industries evaluating DC04 cold-rolled steel against specification 
        LSQ-SPEC-DC04-r3. You output only valid JSON. Never add commentary 
        outside the JSON object.""",
        template=f"""{prompt}

((extracted_json))""",
        model=["claude-sonnet-4-20250514"],
        temperature=0.0,
        max_tokens=1000,
    )

    return conditional_node


def build_fail_node(workflow_def):
    prompt = load_prompt("check_fail.txt")

    fail_node = workflow_def.node("TextGenerationNode").config(
        system_prompt="""You are a supplier quality inspector for Lusotech 
        Industries evaluating DC04 cold-rolled steel against specification 
        LSQ-SPEC-DC04-r3. You output only valid JSON. Never add commentary 
        outside the JSON object.""",
        template=f"""{prompt}

((extracted_json))""",
        model=["claude-sonnet-4-20250514"],
        temperature=0.0,
        max_tokens=1000,
    )

    return fail_node