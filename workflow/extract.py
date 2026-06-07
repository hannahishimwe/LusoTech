from pathlib import Path

def load_prompt(filename: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / filename
    with open(prompt_path, "r") as f:
        return f.read()

def build_extraction_node(workflow_def):
    prompt = load_prompt("extract.txt")
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="You are a data extraction engine. Output ONLY a raw JSON object. No markdown, no code fences, no backticks, no prose. Start your response with { and end with }.",
        template=f"""{prompt}

Email body:
((email_body))

Attachment text:
((attachment))""",
        model=["claude-4.5-sonnet"],
        temperature=0.0,
        max_tokens=2000,
        inputs={"variables": {"keys": ["email_body", "attachment"]}},
    )
    

def build_extraction_passthrough_node(workflow_def):
    return workflow_def.node("TextGenerationNode").config(
        system_prompt="You are a passthrough node. Output the input exactly as received. Never wrap in markdown, never add backticks, never add code fences. Output raw JSON only.",
        template="""
        Output the input exactly as received. No changes. No formatting. No commentary. No markdown. Just the raw JSON string.
        ((extracted_json))""",
        model=["claude-4.5-sonnet"],
        temperature=0.0,
        max_tokens=1000,
        inputs={"variables": {"keys": ["extracted_json"]}},
    )