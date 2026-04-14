from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prompt_app.parser import build_prompt_records, save_prompt_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export prompts from Prompts.docx to JSON.")
    parser.add_argument("--docx", default="Prompts.docx", help="Path to the source DOCX file.")
    parser.add_argument("--output", default="data/prompts.json", help="Path to the output JSON file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    docx_path = Path(args.docx).resolve()
    output_path = Path(args.output).resolve()

    records = build_prompt_records(docx_path)
    save_prompt_records(records, output_path)
    print(f"Exported {len(records)} prompts to {output_path}")


if __name__ == "__main__":
    main()
