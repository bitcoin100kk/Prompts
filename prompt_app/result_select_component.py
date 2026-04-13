from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).resolve().parent / 'components' / 'result_select_copy'
_result_select_component = components.declare_component(
    'result_select_copy',
    path=str(_COMPONENT_DIR),
)


def render_result_select_component(
    *,
    prompt_id: str,
    title: str,
    content: str,
    selected: bool,
    key: str,
) -> str | None:
    value = _result_select_component(
        prompt_id=prompt_id,
        title=title,
        content=content,
        selected=selected,
        key=key,
        default=None,
    )
    return value if isinstance(value, str) else None
