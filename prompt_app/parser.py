from __future__ import annotations

import json
import re
import unicodedata
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
TITLE_STYLE = "Title"
HEADING2_STYLE = "Heading2"


@dataclass(slots=True)
class Paragraph:
    style: str
    text: str


@dataclass(slots=True)
class Section:
    title: str
    paragraphs: list[Paragraph]


@dataclass(slots=True)
class PromptRecord:
    id: str
    slug: str
    title: str
    category: str
    use_case: str
    description: str
    tags: list[str]
    aliases: list[str]
    status: str
    last_updated: str
    owner: str | None
    variables: list[str]
    favorite: bool
    pinned: bool
    content: str
    source_title: str
    source_heading: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


SECTION_METADATA: dict[str, dict] = {
    "prompt-engineer": {
        "title": "Prompt Engineer",
        "category": "Prompting",
        "use_case": "Rewrite raw requests into stronger, model-ready prompts.",
        "description": "A meta prompt for turning underspecified requests into practical prompts with clearer objectives, constraints, and output rules.",
        "tags": ["prompting", "meta prompt", "prompt rewrite", "reasoning"],
        "aliases": ["prompt optimizer", "make this prompt better", "prompt rewriter"],
        "pinned": True,
        "variables": ["PASTE REQUEST HERE"],
    },
    "general": {
        "title": "General",
        "category": "General",
        "use_case": "General-purpose analysis, strategy, and decision support with a high rigor bar.",
        "description": "A strong default prompt for ambiguous questions where correctness, practical value, and explicit tradeoffs matter more than style.",
        "tags": ["generalist", "analysis", "strategy", "decision support"],
        "aliases": ["default analyst", "general reasoning", "rigorous answer"],
        "pinned": True,
    },
    "summarizer-general": {
        "title": "Summarizer (General)",
        "category": "General",
        "use_case": "Create continuity-grade handoff summaries for broad conversations.",
        "description": "Optimized for recoverability and continuity when a future session needs a dense, loss-minimized summary of prior discussion.",
        "tags": ["summary", "handoff", "continuity", "archivist"],
        "aliases": ["conversation summary", "handoff summary", "continuation brief"],
    },
    "takeover-general": {
        "title": "Takeover (general)",
        "category": "General",
        "use_case": "Forensic takeover and continuity handoff for prompt-library project state.",
        "description": "Structured takeover prompt focused on preserving implementation context, risks, and exact continuation steps.",
        "tags": ["takeover", "handoff", "continuity", "general"],
        "aliases": ["project takeover", "forensic handoff", "continuation takeover"],
    },
    "zip-file-general": {
        "title": "Zip File (general)",
        "category": "General",
        "use_case": "Inspect and recover project context from archive files with high-fidelity extraction.",
        "description": "Prompt for archive-first recovery workflows where source state is inside zip artifacts and needs structured analysis.",
        "tags": ["zip", "archive", "recovery", "general"],
        "aliases": ["zip inspection", "archive analysis", "zip takeover"],
    },
    "computer-science": {
        "title": "Computer Science",
        "category": "Engineering",
        "use_case": "Answer coding, systems, debugging, and architecture questions with production-grade rigor.",
        "description": "A technical reasoning prompt that prioritizes correctness, robustness, security, maintainability, and operational reality.",
        "tags": ["coding", "debugging", "architecture", "systems"],
        "aliases": ["software engineering", "technical architect", "debug code"],
        "pinned": True,
    },
    "ui-engineer": {
        "title": "UI Engineer",
        "category": "Product Design",
        "use_case": "Critique or redesign interfaces with emphasis on usability, accessibility, and conversion.",
        "description": "Focuses on interface friction, task completion, clarity, and the smallest realistic changes that improve the product materially.",
        "tags": ["ui", "ux", "design critique", "redesign"],
        "aliases": ["interface review", "product design", "ux review"],
    },
    "quant": {
        "title": "Quant",
        "category": "Quantitative",
        "use_case": "Handle trading, modeling, and quantitative research with explicit assumptions and rigor.",
        "description": "Useful for market analysis, statistical reasoning, quantitative system design, and trading-related engineering questions.",
        "tags": ["quant", "trading", "research", "statistics"],
        "aliases": ["quantitative analysis", "trading system", "market research"],
    },
    "summarizer-quant": {
        "title": "Summarizer (Quant)",
        "category": "Quantitative",
        "use_case": "Create engineering-grade handoff summaries for technical and coding conversations.",
        "description": "Built for preserving implementation details, debugging history, architecture, tooling, and unresolved engineering issues.",
        "tags": ["technical summary", "engineering handoff", "code summary", "continuity"],
        "aliases": ["software handoff", "engineering recap", "technical archivist"],
    },
    "life": {
        "title": "Life",
        "category": "Life",
        "use_case": "Handle reflective or life-decision questions with philosophical depth but without framework abuse.",
        "description": "Applies philosophical lenses selectively and only when they materially improve advice, reflection, or ethical reasoning.",
        "tags": ["life advice", "reflection", "philosophy", "decision making"],
        "aliases": ["philosophical council", "meaning", "identity questions"],
    },
    "summarizer-life": {
        "title": "Summarizer (Life)",
        "category": "Life",
        "use_case": "Preserve long-running personal context and continuity for future conversations.",
        "description": "Designed to maintain identity, patterns, open loops, and emotional logic with evidence discipline and continuity fidelity.",
        "tags": ["personal summary", "continuity", "memory", "relationship context"],
        "aliases": ["life handoff", "continuity archive", "personal memory summary"],
    },
    "communication": {
        "title": "Communication",
        "category": "Communication",
        "use_case": "Draft or critique negotiation, writing, messaging, and high-stakes communication.",
        "description": "Optimized for credibility, leverage, truthfulness, and strategic clarity in emails, messages, and negotiation scenarios.",
        "tags": ["writing", "negotiation", "email", "messaging"],
        "aliases": ["cold email", "message rewrite", "negotiation help"],
        "pinned": True,
    },
    "health": {
        "title": "Health",
        "category": "Health",
        "use_case": "Evaluate foods, supplements, and health-oriented products with practical skepticism.",
        "description": "Focuses on product quality, ingredients, real tradeoffs, and decision usefulness instead of branding or wellness marketing.",
        "tags": ["nutrition", "shopping", "supplements", "food"],
        "aliases": ["healthy shopping", "food review", "supplement review"],
    },
    "skin": {
        "title": "Skin",
        "category": "Health",
        "use_case": "Plan skincare and facial aesthetics decisions with realism and evidence awareness.",
        "description": "Balances visible skin improvement, barrier integrity, practicality, and realistic expectations.",
        "tags": ["skincare", "appearance", "routine", "aesthetics"],
        "aliases": ["skin routine", "face care", "appearance optimization"],
    },
    "legal-tax": {
        "title": "Legal / Tax",
        "category": "Legal / Tax",
        "use_case": "Spot legal, tax, structuring, compliance, and contract risks early.",
        "description": "A risk-focused prompt for reviewing agreements, business structures, compliance exposure, and tax-sensitive decisions.",
        "tags": ["legal", "tax", "contracts", "compliance"],
        "aliases": ["contract review", "llc", "tax strategy", "legal risk"],
    },
    "technician": {
        "title": "Technician",
        "category": "Technical",
        "use_case": "Diagnose mechanical, electrical, and system failures using a real troubleshooting mindset.",
        "description": "Useful for failure analysis, wiring issues, electronics, and field diagnostics where symptoms need to be separated from root cause.",
        "tags": ["diagnostics", "mechanical", "electrical", "troubleshooting"],
        "aliases": ["repair diagnosis", "failure analysis", "troubleshoot system"],
    },
    "contractor": {
        "title": "Contractor",
        "category": "Home Improvement",
        "use_case": "Plan residential renovation or building decisions with systems-level thinking.",
        "description": "Covers home improvement strategy, contractor review, estimating, quality control, and renovation risk management.",
        "tags": ["home improvement", "contractor", "renovation", "construction"],
        "aliases": ["bid review", "house project", "renovation planning"],
    },
    "landscape": {
        "title": "Landscape",
        "category": "Home Improvement",
        "use_case": "Plan drainage, grading, sitework, and turf establishment without creating hidden yard problems.",
        "description": "Targets erosion, water flow, grading, drainage, soil prep, and practical landscape execution decisions.",
        "tags": ["drainage", "grading", "yard", "turf"],
        "aliases": ["sitework", "yard drainage", "erosion control", "land grading"],
    },
}


HEADING_METADATA: dict[tuple[str, str], dict] = {
    ("business", "prompt-1-opportunity-filter-not-idea-generator"): {
        "title": "Opportunity Filter, not Idea Generator",
        "category": "Business",
        "use_case": "Pressure-test business ideas for painful problems, reachable buyers, and a fast path to first revenue.",
        "description": "A skeptical business screening prompt that rejects weak opportunities and forces evidence-aware validation.",
        "tags": ["business", "startup", "idea filter", "first revenue"],
        "aliases": ["business idea validation", "startup idea filter", "opportunity filter"],
        "pinned": True,
    },
    ("business-prompt-2-addon", "prompt-2-14-day-validation-sprint-for-first-revenue"): {
        "title": "14-Day Validation Sprint for First Revenue",
        "category": "Business",
        "use_case": "Turn a chosen business idea into a short validation sprint focused on real buying signal.",
        "description": "Builds a concrete outreach-first validation plan aimed at deposits, paid pilots, and other real commitment signals.",
        "tags": ["business", "validation", "first revenue", "outreach"],
        "aliases": ["validation sprint", "paid pilot", "customer discovery plan"],
    },
    ("optional-initial-prompt-addon", "optional-founder-input-bloc"): {
        "title": "Founder Input Block",
        "category": "Business",
        "use_case": "Template for collecting founder context before business ideation or validation.",
        "description": "A lightweight input block for capturing skills, constraints, assets, and preferences before running the business prompts.",
        "tags": ["business", "founder profile", "inputs", "template"],
        "aliases": ["founder context", "startup intake", "business inputs"],
        "variables": [
            "Skills",
            "Domains / workflows I know well",
            "Communities / audience / network I can reach",
            "Assets I already have",
            "Budget",
            "Hours per week",
            "Technical ability",
            "Geography / legal / language constraints",
            "Income goal and time horizon",
            "Preferred business model",
            "What I am willing and unwilling to do",
            "Risk tolerance",
        ],
    },
}


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return cleaned or "prompt"


def read_docx_paragraphs(docx_path: Path) -> list[Paragraph]:
    with zipfile.ZipFile(docx_path) as archive:
        document_xml = archive.read("word/document.xml")

    document = ET.fromstring(document_xml)
    paragraphs: list[Paragraph] = []
    for paragraph in document.findall(".//w:body/w:p", WORD_NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", WORD_NS)).strip()
        if not text:
            continue
        style = ""
        properties = paragraph.find("w:pPr", WORD_NS)
        if properties is not None:
            style_node = properties.find("w:pStyle", WORD_NS)
            if style_node is not None:
                style = style_node.attrib.get(f"{{{WORD_NS['w']}}}val", "")
        paragraphs.append(Paragraph(style=style, text=text))
    return paragraphs


def group_sections(paragraphs: Iterable[Paragraph]) -> list[Section]:
    sections: list[Section] = []
    current_title: str | None = None
    current_body: list[Paragraph] = []

    for paragraph in paragraphs:
        if paragraph.style == TITLE_STYLE:
            if current_title is not None:
                sections.append(Section(title=current_title, paragraphs=current_body))
            current_title = paragraph.text
            current_body = []
            continue
        if current_title is not None:
            current_body.append(paragraph)

    if current_title is not None:
        sections.append(Section(title=current_title, paragraphs=current_body))
    return sections


def infer_prompt_title(section: Section) -> tuple[str, str | None, list[Paragraph]]:
    if section.paragraphs and section.paragraphs[0].style == HEADING2_STYLE:
        heading = section.paragraphs[0].text
        return heading, heading, section.paragraphs[1:]
    return section.title, None, section.paragraphs


def lookup_metadata(section_title: str, heading: str | None) -> dict:
    section_key = slugify(section_title)
    if heading:
        metadata = HEADING_METADATA.get((section_key, slugify(heading)))
        if metadata:
            return metadata
    return SECTION_METADATA.get(section_key, {})


def shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    clipped = text[: limit - 3].rsplit(" ", 1)[0].strip()
    return f"{clipped}..."


def pick_use_case(lines: list[str], fallback_title: str) -> str:
    for line in lines:
        candidate = line.strip()
        if not candidate:
            continue
        if candidate.endswith(":") and len(candidate) < 80:
            continue
        return shorten(candidate, 140)
    return f"Reference prompt for {fallback_title}."


def pick_description(lines: list[str], fallback_use_case: str) -> str:
    meaningful = []
    for line in lines:
        candidate = line.strip()
        if not candidate:
            continue
        if candidate == fallback_use_case:
            continue
        meaningful.append(candidate)
        if len(meaningful) == 2:
            break
    if meaningful:
        return shorten(" ".join(meaningful), 220)
    return fallback_use_case


def compose_content(paragraphs: list[Paragraph]) -> str:
    return "\n".join(paragraph.text for paragraph in paragraphs).strip()


def extract_variables(content: str) -> list[str]:
    variables: list[str] = []
    seen: set[str] = set()

    for match in re.findall(r"\[([^\[\]]+)\]", content):
        cleaned = match.strip()
        if cleaned and cleaned not in seen:
            variables.append(cleaned)
            seen.add(cleaned)

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and stripped.endswith(":"):
            candidate = stripped[2:-1].strip()
            if 1 < len(candidate) <= 80 and candidate not in seen:
                variables.append(candidate)
                seen.add(candidate)
    return variables


def cleanup_prompt_title(text: str) -> str:
    cleaned = re.sub(r"^Prompt\s+\d+\s+[—-]\s+", "", text, flags=re.IGNORECASE)
    return cleaned.strip().rstrip(":")


def infer_tags(title: str, category: str) -> list[str]:
    words = [word for word in re.split(r"[^a-zA-Z0-9]+", f"{title} {category}".lower()) if word]
    seen: set[str] = set()
    tags: list[str] = []
    for word in words:
        if len(word) < 3 or word in seen:
            continue
        tags.append(word)
        seen.add(word)
        if len(tags) == 4:
            break
    return tags or [slugify(category)]


def build_prompt_records(docx_path: Path, owner: str | None = None) -> list[PromptRecord]:
    paragraphs = read_docx_paragraphs(docx_path)
    sections = group_sections(paragraphs)
    last_updated = datetime.fromtimestamp(docx_path.stat().st_mtime).date().isoformat()

    prompts: list[PromptRecord] = []
    slug_counts: dict[str, int] = {}

    for section in sections:
        raw_title, heading, content_paragraphs = infer_prompt_title(section)
        metadata = lookup_metadata(section.title, heading)

        title = metadata.get("title", cleanup_prompt_title(raw_title))
        category = metadata.get("category", cleanup_prompt_title(section.title).title())
        content = compose_content(content_paragraphs)
        content_lines = [line for line in content.splitlines() if line.strip()]
        use_case = metadata.get("use_case", pick_use_case(content_lines, title))
        description = metadata.get("description", pick_description(content_lines, use_case))
        tags = list(metadata.get("tags", infer_tags(title, category)))
        aliases = list(metadata.get("aliases", []))
        variables = list(metadata.get("variables", extract_variables(content)))

        slug = metadata.get("slug", slugify(title))
        slug_counts[slug] = slug_counts.get(slug, 0) + 1
        if slug_counts[slug] > 1:
            slug = f"{slug}-{slug_counts[slug]}"

        prompts.append(
            PromptRecord(
                id=f"prompt-{slug}",
                slug=slug,
                title=title,
                category=category,
                use_case=use_case,
                description=description,
                tags=tags,
                aliases=aliases,
                status=metadata.get("status", "active"),
                last_updated=last_updated,
                owner=owner,
                variables=variables,
                favorite=metadata.get("favorite", False),
                pinned=metadata.get("pinned", False),
                content=content,
                source_title=section.title,
                source_heading=heading,
            )
        )

    return prompts


def save_prompt_records(records: list[PromptRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [record.to_dict() for record in records]
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
