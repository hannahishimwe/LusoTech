
"""
Exports the Lusotech SQE workflow from staging and imports it into a target workspace.
"""

import argparse
import json
import sys
from noxus_sdk.client import Client
from config import get_noxus_config
from noxus_sdk.workflows import WorkflowDefinition

WORKFLOW_ID = "23348f7f-7b3e-4973-8f89-f205836c7f61"
SOURCE_API_KEY = get_noxus_config().api_key


def export_workflow(client: Client) -> str:
    print(f"Fetching workflow {WORKFLOW_ID}...")
    wf = client.workflows.get(WORKFLOW_ID)
    print(f"Fetched: '{wf.name}'")
    return wf.model_dump_json()



def import_workflow(client: Client, workflow_json: str, overwrite: bool) -> None:
    wf = WorkflowDefinition.model_validate_json(workflow_json)

    for existing in client.workflows.list():
        if existing.name == wf.name:
            if overwrite:
                print(f"'{wf.name}' already exists (id: {existing.id}). Overwriting...")
                client.workflows.delete(existing.id)
            else:
                print(f"'{wf.name}' already exists. Run with --overwrite to replace.")
                sys.exit(1)
            break

    saved = client.workflows.save(wf)
    print(f"Imported successfully (id: {saved.id})")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Lusotech SQE workflow from staging to a target Noxus workspace."
    )
    parser.add_argument("--target-api-key", required=True, help="Target workspace API key")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite if workflow already exists in target")
    args = parser.parse_args()

    source_client = Client(api_key=SOURCE_API_KEY)
    target_client = Client(api_key=args.target_api_key)

    workflow_def = export_workflow(source_client)
    import_workflow(target_client, workflow_def, args.overwrite)

    print("Done.")


if __name__ == "__main__":
    main()