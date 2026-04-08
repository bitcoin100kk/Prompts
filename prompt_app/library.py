from __future__ import annotations

import json
from pathlib import Path

from prompt_app.parser import build_prompt_records, save_prompt_records


DOCX_NAME = "Prompts.docx"
JSON_RELATIVE_PATH = Path("data") / "prompts.json"


def get_source_status(base_dir: Path) -> dict:
    docx_path = base_dir / DOCX_NAME
    json_path = base_dir / JSON_RELATIVE_PATH
    return {
        "docx_path": docx_path,
        "json_path": json_path,
        "docx_exists": docx_path.exists(),
        "json_exists": json_path.exists(),
        "docx_is_newer": docx_path.exists() and json_path.exists() and docx_path.stat().st_mtime > json_path.stat().st_mtime,
    }


def rebuild_prompt_json(base_dir: Path) -> list[dict]:
    status = get_source_status(base_dir)
    if not status["docx_exists"]:
        raise FileNotFoundError(f"Missing source document: {status['docx_path']}")

    records = build_prompt_records(status["docx_path"])
    save_prompt_records(records, status["json_path"])
    return [record.to_dict() for record in records]


def load_prompts(base_dir: Path) -> tuple[list[dict], dict]:
    status = get_source_status(base_dir)
    if status["json_exists"]:
        prompts = json.loads(status["json_path"].read_text(encoding="utf-8"))
        return prompts, status

    prompts = rebuild_prompt_json(base_dir)
    return prompts, get_source_status(base_dir)
