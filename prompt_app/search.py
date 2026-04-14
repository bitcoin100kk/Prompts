from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", normalize_text(text)) if token]


def filter_prompts(
    prompts: list[dict],
    *,
    category: str,
    statuses: list[str],
    favorites_only: bool,
    pinned_only: bool,
) -> list[dict]:
    allowed_statuses = {status.lower() for status in statuses}
    results: list[dict] = []
    for prompt in prompts:
        if category != "All" and prompt["category"] != category:
            continue
        if prompt["status"].lower() not in allowed_statuses:
            continue
        if favorites_only and not prompt["favorite"]:
            continue
        if pinned_only and not prompt["pinned"]:
            continue
        results.append(prompt)
    return results


def _score_exact_contains(query: str, value: str, *, exact: int, prefix: int, contains: int) -> int:
    if not query or not value:
        return 0
    if value == query:
        return exact
    if value.startswith(query):
        return prefix
    if query in value:
        return contains
    return 0


def _score_token_hits(tokens: list[str], value: str, weight: int, cap: int) -> int:
    if not tokens or not value:
        return 0
    hits = sum(1 for token in tokens if token in value)
    return min(hits * weight, cap)


def score_prompt(prompt: dict, query: str, recent_prompt_ids: list[str]) -> int:
    query_normalized = normalize_text(query)
    tokens = tokenize(query)

    if not query_normalized:
        score = 0
        score += 35 if prompt["pinned"] else 0
        score += 20 if prompt["favorite"] else 0
        score += 12 if prompt["id"] in recent_prompt_ids else 0
        return score

    fields = {
        "title": normalize_text(prompt["title"]),
        "category": normalize_text(prompt["category"]),
        "use_case": normalize_text(prompt["use_case"]),
        "description": normalize_text(prompt["description"]),
        "content": normalize_text(prompt["content"]),
        "aliases": [normalize_text(alias) for alias in prompt["aliases"]],
        "tags": [normalize_text(tag) for tag in prompt["tags"]],
    }

    score = 0
    score += _score_exact_contains(query_normalized, fields["title"], exact=130, prefix=95, contains=75)
    score += _score_token_hits(tokens, fields["title"], weight=22, cap=66)

    for alias in fields["aliases"]:
        score += _score_exact_contains(query_normalized, alias, exact=75, prefix=58, contains=48)
        score += _score_token_hits(tokens, alias, weight=16, cap=32)

    for tag in fields["tags"]:
        score += _score_exact_contains(query_normalized, tag, exact=60, prefix=48, contains=42)
        score += _score_token_hits(tokens, tag, weight=14, cap=28)

    score += _score_exact_contains(query_normalized, fields["category"], exact=40, prefix=28, contains=24)
    score += _score_exact_contains(query_normalized, fields["use_case"], exact=35, prefix=30, contains=26)
    score += _score_token_hits(tokens, fields["use_case"], weight=11, cap=33)
    score += _score_exact_contains(query_normalized, fields["description"], exact=24, prefix=20, contains=18)
    score += _score_token_hits(tokens, fields["description"], weight=8, cap=24)
    score += _score_exact_contains(query_normalized, fields["content"], exact=14, prefix=10, contains=8)
    score += _score_token_hits(tokens, fields["content"], weight=4, cap=20)

    if prompt["status"] == "deprecated":
        score -= 80
    if prompt["pinned"]:
        score += 18
    if prompt["favorite"]:
        score += 10
    if prompt["id"] in recent_prompt_ids:
        score += 8

    return score


def search_prompts(prompts: list[dict], *, query: str, recent_prompt_ids: list[str]) -> list[dict]:
    ranked: list[tuple[int, dict]] = []
    for prompt in prompts:
        score = score_prompt(prompt, query, recent_prompt_ids)
        if query.strip() and score <= 0:
            continue
        ranked.append((score, prompt))

    ranked.sort(
        key=lambda item: (
            -item[0],
            -int(item[1]["pinned"]),
            -int(item[1]["favorite"]),
            item[1]["title"].lower(),
        )
    )
    return [prompt for _, prompt in ranked]
