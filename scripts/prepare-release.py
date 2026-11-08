#!/usr/bin/env python3
"""Prepare a development workflow export for the local practice n8n instance.

The development and practice instances have independent workflow and credential
IDs. This script keeps the development workflow logic while remapping the known
workflow/node/credential references to the corresponding practice-instance IDs.
It fails closed if a credentialed node cannot be matched by name and type.
"""

import argparse
import json
import os
from pathlib import Path
import re


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def unique_nodes(workflow: dict, path: Path) -> dict[str, dict]:
    result = {}
    for node in workflow.get("nodes", []):
        name = node.get("name")
        if not name or name in result:
            raise ValueError(f"Node names must be present and unique in {path}")
        result[name] = node
    return result


def prepare(source: dict, target: dict, source_path: Path, target_path: Path) -> dict:
    if source.get("name") != target.get("name"):
        raise ValueError("Source and practice exports have different workflow names")
    if not target.get("id"):
        raise ValueError("Practice export is missing its workflow ID")

    source_nodes = unique_nodes(source, source_path)
    target_nodes = unique_nodes(target, target_path)
    release = json.loads(json.dumps(source))
    release["id"] = target["id"]

    contact_email = os.environ.get("SEC_USER_AGENT_EMAIL", "").strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", contact_email):
        raise ValueError("Set SEC_USER_AGENT_EMAIL to a valid contact email in the runner environment")
    placeholder = "your-email@example.com"
    replaced_contact = False

    for node in release.get("nodes", []):
        target_node = target_nodes.get(node.get("name"))
        if target_node is None:
            # New development nodes keep their development-generated IDs.
            if node.get("credentials"):
                raise ValueError(
                    f"New credentialed node {node.get('name')!r} needs a credential set up and mapped in the practice instance first"
                )
            continue

        source_credentials = node.get("credentials") or {}
        target_credentials = target_node.get("credentials") or {}
        if set(source_credentials) != set(target_credentials):
            raise ValueError(
                f"Credential types differ for node {node.get('name')!r}; update the practice mapping before deployment"
            )

        # Keep practice node identity and credential IDs while using the source
        # node configuration, parameters, and connections.
        for key in ("id", "webhookId"):
            if key in target_node:
                node[key] = target_node[key]
        if target_credentials:
            node["credentials"] = target_credentials
        else:
            node.pop("credentials", None)

        # Keep contact details out of the public workflow export; supply them
        # privately through a GitHub Actions secret at deployment time.
        headers = (
            node.get("parameters", {})
            .get("headerParameters", {})
            .get("parameters", [])
        )
        for header in headers:
            if header.get("name", "").lower() == "user-agent":
                value = header.get("value", "")
                if placeholder in value:
                    header["value"] = value.replace(placeholder, contact_email)
                    replaced_contact = True

    if not replaced_contact:
        raise ValueError("Could not find the SEC User-Agent email placeholder in the source workflow")

    # Confirm every source credentialed node had a matching practice node.
    for name, node in source_nodes.items():
        if node.get("credentials") and name not in target_nodes:
            raise ValueError(f"Credentialed node {name!r} is missing from the practice export")

    return release


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    release = prepare(
        read_json(args.source), read_json(args.target), args.source, args.target
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    print(
        f"Prepared {release['name']!r} for the practice instance "
        f"({len(release.get('nodes', []))} nodes)."
    )


if __name__ == "__main__":
    main()
