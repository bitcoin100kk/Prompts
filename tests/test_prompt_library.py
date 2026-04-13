from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DOCX_PATH = BASE_DIR / "Prompts.docx"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import split_recent_results
from prompt_app.parser import build_prompt_records
from prompt_app.search import search_prompts


class PromptLibraryTests(unittest.TestCase):
    def test_docx_parses_into_expected_prompt_count(self) -> None:
        prompts = build_prompt_records(DOCX_PATH)
        self.assertGreaterEqual(len(prompts), 19)

    def test_business_prompt_is_present(self) -> None:
        prompts = build_prompt_records(DOCX_PATH)
        titles = {prompt.title for prompt in prompts}
        self.assertIn("Opportunity Filter, not Idea Generator", titles)

    def test_search_finds_communication_prompt(self) -> None:
        prompts = [prompt.to_dict() for prompt in build_prompt_records(DOCX_PATH)]
        ranked = search_prompts(prompts, query="cold email negotiation message", recent_prompt_ids=[])
        self.assertGreater(len(ranked), 0)
        self.assertEqual(ranked[0]["title"], "Communication")

    def test_search_finds_legal_tax_prompt(self) -> None:
        prompts = [prompt.to_dict() for prompt in build_prompt_records(DOCX_PATH)]
        ranked = search_prompts(prompts, query="llc tax contract risk", recent_prompt_ids=[])
        self.assertGreater(len(ranked), 0)
        self.assertEqual(ranked[0]["title"], "Legal / Tax")

    def test_recent_results_are_partitioned_without_duplication(self) -> None:
        results = [
            {"id": "prompt-a", "title": "A"},
            {"id": "prompt-b", "title": "B"},
            {"id": "prompt-c", "title": "C"},
        ]
        recent_prompts, remaining = split_recent_results(results, ["prompt-c", "prompt-a"], query="")

        self.assertEqual([prompt["id"] for prompt in recent_prompts], ["prompt-c", "prompt-a"])
        self.assertEqual([prompt["id"] for prompt in remaining], ["prompt-b"])


if __name__ == "__main__":
    unittest.main()
