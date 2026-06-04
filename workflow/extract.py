from pathlib import Path

def load_prompt(filename: str) -> str:
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / filename
    with open(prompt_path, "r") as f:
        return f.read()

def build_extraction_node(workflow_def):
    prompt = load_prompt("extract.txt")
    
    extraction_node = workflow_def.node("TextGenerationNode").config(
        system_prompt="""You are a precise document data extraction assistant 
        for Lusotech Industries supplier quality process. You extract Certificate 
        of Analysis data and return only valid JSON. Never add commentary outside 
        the JSON object.""",
        template=f"""{prompt}

Email body:
((email_body))

CoA Document:
((coa_document))""",
        model=["claude-sonnet-4-20250514"],
        temperature=0.0,
        max_tokens=2000,
    )
    
    return extraction_node