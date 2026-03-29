#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

import httpx


OPENAI_FILES_URL = "https://api.openai.com/v1/files"
OPENAI_VECTOR_STORES_URL = "https://api.openai.com/v1/vector_stores"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload bug support knowledge files to an OpenAI vector store.")
    parser.add_argument(
        "--kb-dir",
        default="docs/support-kb/bugs",
        help="Directory containing markdown support KB files.",
    )
    parser.add_argument(
        "--vector-store-id",
        default=os.getenv("OPENAI_SUPPORT_VECTOR_STORE_ID", ""),
        help="Existing vector store ID to reuse. If omitted, a new store is created.",
    )
    parser.add_argument(
        "--name",
        default="InvoiceBot Bug Support KB",
        help="Vector store name when creating a new store.",
    )
    return parser.parse_args()


def require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required.")
    return api_key


def kb_files(directory: str) -> list[Path]:
    root = Path(directory)
    if not root.exists():
        raise SystemExit(f"Knowledge base directory not found: {root}")
    files = sorted(path for path in root.rglob("*.md") if path.is_file())
    if not files:
        raise SystemExit(f"No markdown files found in: {root}")
    return files


def create_vector_store(client: httpx.Client, name: str) -> str:
    response = client.post(OPENAI_VECTOR_STORES_URL, json={"name": name})
    response.raise_for_status()
    payload = response.json()
    return str(payload["id"])


def upload_file(client: httpx.Client, path: Path) -> str:
    with path.open("rb") as handle:
        response = client.post(
            OPENAI_FILES_URL,
            data={"purpose": "assistants"},
            files={"file": (path.name, handle, "text/markdown")},
        )
    response.raise_for_status()
    return str(response.json()["id"])


def attach_file(client: httpx.Client, vector_store_id: str, file_id: str) -> str:
    response = client.post(f"{OPENAI_VECTOR_STORES_URL}/{vector_store_id}/files", json={"file_id": file_id})
    response.raise_for_status()
    return str(response.json()["id"])


def main() -> None:
    args = parse_args()
    api_key = require_api_key()
    files = kb_files(args.kb_dir)

    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(headers=headers, timeout=60.0) as client:
        vector_store_id = args.vector_store_id or create_vector_store(client, args.name)
        print(f"Using vector store: {vector_store_id}")
        for path in files:
            file_id = upload_file(client, path)
            vector_file_id = attach_file(client, vector_store_id, file_id)
            print(f"Uploaded {path} -> file {file_id} -> vector file {vector_file_id}")

    print("\nSet this in Railway:")
    print(f"OPENAI_SUPPORT_VECTOR_STORE_ID={vector_store_id}")


if __name__ == "__main__":
    main()
