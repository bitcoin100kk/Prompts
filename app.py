from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from prompt_app.library import load_prompts, rebuild_prompt_json
from prompt_app.search import filter_prompts, search_prompts


BASE_DIR = Path(__file__).resolve().parent
DOCX_PATH = BASE_DIR / "Prompts.docx"
JSON_PATH = BASE_DIR / "data" / "prompts.json"
MAX_RESULTS = 50


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --card-bg: #0b1324;
            --card-border: #18233b;
            --card-border-active: #2b4b9a;
            --text-muted: #93a1bb;
            --title: #e9eefb;
            --accent: #2d63f0;
        }
        .block-container {
            padding-top: 0.65rem;
            padding-bottom: 0.75rem;
        }
        .toolbar-note {
            color: var(--text-muted);
            font-size: 0.82rem;
            margin: 0.2rem 0 0.55rem;
            letter-spacing: 0.01em;
        }
        .prompt-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.28rem;
            margin: 0.2rem 0 0;
        }
        .prompt-chip {
            display: inline-block;
            padding: 0.14rem 0.46rem;
            border-radius: 999px;
            background: #101d36;
            color: #9ab3f0;
            font-size: 0.72rem;
            line-height: 1.2;
            border: 1px solid #24375c;
        }
        .prompt-chip.status-deprecated {
            background: #30131d;
            color: #f3a8b4;
            border-color: #6d2036;
        }
        .prompt-chip.status-draft {
            background: #2e2210;
            color: #f5c08e;
            border-color: #714712;
        }
        .inline-note {
            color: #93a1bb;
            font-size: 0.82rem;
            margin: 0.25rem 0 0.55rem;
        }
        .variables-callout {
            border: 1px solid #2a3f6b;
            border-radius: 0.72rem;
            padding: 0.62rem 0.72rem;
            background: #101d36;
            margin: 0.55rem 0;
        }
        .variables-title {
            color: #8fb0ff;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.34rem;
        }
        .variable-chip {
            display: inline-block;
            margin: 0.12rem 0.28rem 0.1rem 0;
            padding: 0.16rem 0.45rem;
            border-radius: 999px;
            background: #0c162e;
            color: #9ebaf6;
            border: 1px solid #36548d;
            font-size: 0.74rem;
        }
        .prompt-preview {
            border: 1px solid #223253;
            border-radius: 0.78rem;
            padding: 0.8rem 0.86rem;
            background: #0a1222;
            color: #f8fafc;
            max-height: 28rem;
            overflow: auto;
            margin-top: 0.25rem;
        }
        .prompt-preview pre {
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-wrap: anywhere;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.84rem;
            line-height: 1.45;
        }
        .draft-note {
            border: 1px solid #705321;
            border-radius: 0.72rem;
            padding: 0.56rem 0.64rem;
            background: #241d12;
            color: #edc888;
            margin-bottom: 0.5rem;
            font-size: 0.82rem;
        }
        .results-note {
            color: var(--text-muted);
            font-size: 0.78rem;
            margin-bottom: 0.4rem;
        }
        .copy-footer-note {
            color: #93a1bb;
            font-size: 0.78rem;
            margin: 0.58rem 0 0.36rem;
        }
        .quick-copy-note {
            color: #9badcf;
            font-size: 0.77rem;
            margin: 0.22rem 0 0.35rem;
        }
        h2, h3, h4 {
            color: var(--title);
            margin-top: 0.1rem;
        }
        div[data-testid="stTextInputRootElement"] input {
            min-height: 2.35rem;
            padding: 0.45rem 0.72rem;
            border-radius: 0.72rem;
            border: 1px solid #2a3a58;
            font-size: 0.98rem;
            background: #101826;
        }
        div[data-testid="stPopover"] > div > button {
            min-height: 2.25rem;
            border-radius: 0.72rem;
            font-size: 0.95rem;
            font-weight: 600;
            border: 1px solid #22304d;
            background: #0d172d;
            color: #dbe6ff;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--card-border) !important;
            border-radius: 0.9rem !important;
            background: var(--card-bg);
            box-shadow: none !important;
        }
        div[data-testid="stButton"] > button {
            min-height: 2.2rem;
            border-radius: 0.72rem;
            font-size: 1rem;
            font-weight: 600;
            transition: 140ms ease-in-out;
        }
        div[data-testid="stButton"] > button[kind="secondary"] {
            border: 1px solid #2a3a58;
            background: #0f1a32;
            color: #e6ecff;
            box-shadow: none;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            border-color: #3c5688;
            background: #142347;
            color: #f6f9ff;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            border: 1px solid var(--card-border-active);
            background: linear-gradient(180deg, #162a53 0%, #132444 100%);
            color: #f4f7ff;
            box-shadow: inset 3px 0 0 0 var(--accent);
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            border-color: #4167c7;
            background: linear-gradient(180deg, #1a3264 0%, #152d57 100%);
        }
        [data-testid="stCaptionContainer"] {
            color: #96a4bf;
            font-size: 0.84rem;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 0.5rem;
        }
        div[data-testid="stIFrame"] {
            background: #0b1324 !important;
            border: 0 !important;
        }
        div[data-testid="stIFrame"] iframe {
            background: #0b1324 !important;
            border: 0 !important;
            box-shadow: none !important;
        }
        @media (max-width: 900px) {
            .block-container {
                padding-top: 0.45rem;
                padding-left: 0.72rem;
                padding-right: 0.72rem;
                padding-bottom: 0.52rem;
            }
            .prompt-preview {
                max-height: 20rem;
                padding: 0.68rem 0.72rem;
            }
            .prompt-meta {
                gap: 0.22rem;
            }
            div[data-testid="stTextInputRootElement"] input {
                min-height: 2.12rem;
                font-size: 0.95rem;
            }
            div[data-testid="stPopover"] > div > button {
                min-height: 2.04rem;
                font-size: 0.9rem;
            }
            div[data-testid="stButton"] > button {
                min-height: 2.04rem;
                font-size: 0.94rem;
            }
            h2 {
                font-size: 1.7rem;
            }
            h3 {
                font-size: 1.36rem;
            }
            h4 {
                font-size: 1.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_state() -> None:
    defaults = {
        "selected_prompt_id": None,
        "pending_prompt_id": None,
        "edit_mode": False,
        "working_copy_text": "",
        "working_copy_source_prompt_id": None,
        "recent_prompt_ids": [],
        "category_filter": "All",
        "status_filter": ["active"],
        "favorites_only": False,
        "pinned_only": False,
        "query": "",
        "auto_copy_feedback": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def remember_recent(prompt_id: str) -> None:
    recent = [item for item in st.session_state["recent_prompt_ids"] if item != prompt_id]
    recent.insert(0, prompt_id)
    st.session_state["recent_prompt_ids"] = recent[:6]


def sync_working_copy(prompt: dict, force_reset: bool = False) -> None:
    needs_reset = force_reset or st.session_state["working_copy_source_prompt_id"] != prompt["id"]
    if needs_reset:
        st.session_state["working_copy_source_prompt_id"] = prompt["id"]
        st.session_state["working_copy_text"] = prompt["content"]
        if force_reset:
            st.session_state["edit_mode"] = False


def working_copy_is_dirty(prompt: dict) -> bool:
    if st.session_state["working_copy_source_prompt_id"] != prompt["id"]:
        return False
    return st.session_state["working_copy_text"] != prompt["content"]


def resolve_selected_prompt(prompts: list[dict], selected_prompt_id: str | None) -> dict | None:
    by_id = {prompt["id"]: prompt for prompt in prompts}
    if not prompts:
        return None
    if selected_prompt_id and selected_prompt_id in by_id:
        return by_id[selected_prompt_id]

    first = prompts[0]
    st.session_state["selected_prompt_id"] = first["id"]
    sync_working_copy(first, force_reset=True)
    remember_recent(first["id"])
    return first


def request_prompt_switch(target_prompt: dict, current_prompt: dict | None) -> str:
    if current_prompt and target_prompt["id"] == current_prompt["id"]:
        return "same"

    if current_prompt and st.session_state["edit_mode"] and working_copy_is_dirty(current_prompt):
        st.session_state["pending_prompt_id"] = target_prompt["id"]
        return "blocked"

    st.session_state["selected_prompt_id"] = target_prompt["id"]
    st.session_state["pending_prompt_id"] = None
    sync_working_copy(target_prompt, force_reset=True)
    remember_recent(target_prompt["id"])
    return "switched"


def handle_result_tap(target_prompt: dict, current_prompt: dict | None) -> None:
    switch_state = request_prompt_switch(target_prompt, current_prompt)
    if switch_state == "blocked":
        st.session_state["auto_copy_feedback"] = "Unsaved edits detected. Confirm discard to switch prompts."
        st.rerun()
        return
    st.session_state["auto_copy_feedback"] = ""
    if switch_state == "switched":
        st.rerun()


def render_copy_button(label: str, text: str, key: str, *, primary: bool = True) -> None:
    button_label = json.dumps(label)
    payload = json.dumps(text)
    component_surface = "#0b1324"
    background = "linear-gradient(180deg, #1f4fcf 0%, #1b42ab 100%)" if primary else "#12384a"
    border = "#2a64f8" if primary else "#2b6f8b"
    shadow = "inset 3px 0 0 0 #88a7ff" if primary else "inset 3px 0 0 0 #5ab2d3"
    components.html(
        f"""
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="darkreader-lock" />
            <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                background: {component_surface};
                overflow: hidden;
            }}
            #copy-wrap-{key} {{
                width: 100%;
                height: 100%;
                margin: 0;
                padding: 0;
                background: {component_surface};
                border: 0;
                box-shadow: none;
                display: flex;
                align-items: stretch;
            }}
            #copy-button-{key} {{
                width: 100%;
                height: 100%;
                padding: 0.5rem 0.8rem;
                border-radius: 0.72rem;
                border: 1px solid {border};
                background: {background};
                color: #f6f9ff;
                font-weight: 650;
                font-size: 0.95rem;
                line-height: 1.1;
                cursor: pointer;
                box-shadow: {shadow};
                box-sizing: border-box;
                margin: 0;
                display: block;
            }}
            #copy-button-{key}:hover {{
                filter: brightness(1.05);
            }}
            </style>
        </head>
        <body>
            <div id="copy-wrap-{key}">
                <button id="copy-button-{key}" style="width: 100%;">{label}</button>
            </div>
            <script>
            if (!document.head.querySelector('meta[name="darkreader-lock"]')) {{
                const darkreaderLockMeta = document.createElement("meta");
                darkreaderLockMeta.name = "darkreader-lock";
                document.head.appendChild(darkreaderLockMeta);
            }}

            const button = document.getElementById("copy-button-{key}");
            const originalLabel = {button_label};
            const payload = {payload};

            button.addEventListener("click", async () => {{
                try {{
                    await navigator.clipboard.writeText(payload);
                    button.textContent = "Copied";
                    button.style.background = "linear-gradient(180deg, #0d8f63 0%, #0a6f4e 100%)";
                    button.style.borderColor = "#1eb980";
                }} catch (error) {{
                    button.textContent = "Clipboard blocked - press Ctrl+C after selecting text";
                    button.style.background = "#7a4a10";
                    button.style.borderColor = "#a56b22";
                }}

                setTimeout(() => {{
                    button.textContent = originalLabel;
                    button.style.background = "{background}";
                    button.style.borderColor = "{border}";
                }}, 1800);
            }});
            </script>
        </body>
        </html>
        """,
        height=42,
    )


def render_prompt_badges(prompt: dict, *, max_tags: int = 4) -> None:
    tags = "".join(f'<span class="prompt-chip">{html.escape(tag)}</span>' for tag in prompt["tags"][:max_tags])
    status_class = f'prompt-chip status-{prompt["status"]}'
    st.markdown(
        f"""
        <div class="prompt-meta">
            <span class="prompt-chip">{html.escape(prompt["category"])}</span>
            <span class="{status_class}">{prompt["status"].title()}</span>
            {tags}
        </div>
        """,
        unsafe_allow_html=True,
    )


def count_active_filters(prompts: list[dict]) -> int:
    count = 0
    available_statuses = sorted({prompt["status"] for prompt in prompts})
    if st.session_state["category_filter"] != "All":
        count += 1
    if sorted(st.session_state["status_filter"]) != available_statuses:
        count += 1
    if st.session_state["favorites_only"]:
        count += 1
    if st.session_state["pinned_only"]:
        count += 1
    return count


def render_header_controls(prompts: list[dict], source_status: dict) -> bool:
    st.text_input(
        "Search prompts",
        key="query",
        placeholder="Find by task, prompt name, tag, or keyword",
        label_visibility="collapsed",
    )

    filter_count = count_active_filters(prompts)
    filter_label = f"Filters ({filter_count})" if filter_count else "Filters"

    categories = ["All", *sorted({prompt["category"] for prompt in prompts})]
    current_category = st.session_state["category_filter"]
    category_index = categories.index(current_category) if current_category in categories else 0
    available_statuses = sorted({prompt["status"] for prompt in prompts})

    control_left, control_right = st.columns(2, gap="small")
    with control_left:
        with st.popover(filter_label, use_container_width=True):
            st.session_state["category_filter"] = st.selectbox("Category", categories, index=category_index)
            selected_statuses = st.multiselect(
                "Status",
                available_statuses,
                default=st.session_state["status_filter"] or available_statuses,
            )
            st.session_state["status_filter"] = selected_statuses or available_statuses
            st.session_state["favorites_only"] = st.checkbox(
                "Favorites only",
                value=st.session_state["favorites_only"],
            )
            st.session_state["pinned_only"] = st.checkbox(
                "Pinned only",
                value=st.session_state["pinned_only"],
            )

    rebuild_clicked = False
    with control_right:
        with st.popover("Admin", use_container_width=True):
            st.caption(f"JSON source: `{JSON_PATH.name}`")
            if source_status["docx_exists"]:
                st.caption(f"DOCX source: `{DOCX_PATH.name}`")
            if source_status["docx_is_newer"]:
                st.warning("Prompts.docx is newer than prompts.json. Rebuild to sync changes.")
            rebuild_clicked = st.button(
                "Rebuild prompts from DOCX",
                use_container_width=True,
                disabled=not source_status["docx_exists"],
            )
            st.download_button(
                "Download prompts.json",
                JSON_PATH.read_text(encoding="utf-8") if JSON_PATH.exists() else "[]",
                file_name="prompts.json",
                mime="application/json",
                use_container_width=True,
            )

    summary_bits = [f"{len(prompts)} prompts"]
    if filter_count:
        summary_bits.append(f"{filter_count} filters active")
    if source_status["docx_is_newer"]:
        summary_bits.append("DOCX newer than JSON")
    st.markdown(f"<div class='toolbar-note'>{' | '.join(summary_bits)}</div>", unsafe_allow_html=True)

    return rebuild_clicked


def split_recent_results(results: list[dict], recent_prompt_ids: list[str], query: str) -> tuple[list[dict], list[dict]]:
    if query.strip() or not recent_prompt_ids:
        return [], results

    prompt_by_id = {prompt["id"]: prompt for prompt in results}
    recent_prompts = [prompt_by_id[prompt_id] for prompt_id in recent_prompt_ids if prompt_id in prompt_by_id][:4]
    recent_ids = {prompt["id"] for prompt in recent_prompts}
    remaining = [prompt for prompt in results if prompt["id"] not in recent_ids]
    return recent_prompts, remaining


def render_variable_callout(variables: list[str]) -> None:
    chips = "".join(f'<span class="variable-chip">{html.escape(variable)}</span>' for variable in variables)
    st.markdown(
        f"""
        <div class="variables-callout">
            <div class="variables-title">Required inputs / placeholders</div>
            <div>{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_canonical_preview(content: str) -> None:
    escaped = html.escape(content)
    st.markdown(
        f"""
        <div class="prompt-preview">
            <pre>{escaped}</pre>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_results_panel_height(result_count: int) -> int | str:
    return "content"


def render_pending_switch(prompts_by_id: dict[str, dict]) -> None:
    pending_prompt_id = st.session_state["pending_prompt_id"]
    if not pending_prompt_id:
        return

    target_prompt = prompts_by_id[pending_prompt_id]
    st.warning(
        f"You have unsaved edits in the working copy. Switching to '{target_prompt['title']}' will discard them."
    )
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("Discard edits and switch", type="primary", use_container_width=True):
            st.session_state["selected_prompt_id"] = pending_prompt_id
            st.session_state["pending_prompt_id"] = None
            st.session_state["edit_mode"] = False
            sync_working_copy(target_prompt, force_reset=True)
            remember_recent(target_prompt["id"])
            st.rerun()
    with cancel_col:
        if st.button("Keep editing current prompt", use_container_width=True):
            st.session_state["pending_prompt_id"] = None
            st.rerun()


def render_results(results: list[dict], current_prompt: dict | None) -> None:
    st.markdown("### Results")
    if not results:
        st.info("No prompts matched the current search and filters.")
        return
    st.markdown(f"<div class='results-note'>{len(results)} matched</div>", unsafe_allow_html=True)

    recent_prompts, main_results = split_recent_results(
        results,
        st.session_state["recent_prompt_ids"],
        st.session_state["query"],
    )

    if recent_prompts:
        st.markdown("**Recent**")
        for prompt in recent_prompts:
            with st.container(border=True):
                selected = current_prompt and prompt["id"] == current_prompt["id"]
                if st.button(
                    prompt["title"],
                    key=f"recent-{prompt['id']}",
                    use_container_width=True,
                    type="primary" if selected else "secondary",
                ):
                    handle_result_tap(prompt, current_prompt)
                if selected:
                    render_copy_button("Copy selected", prompt["content"], f"quick-recent-{prompt['id']}", primary=True)
                    st.markdown(
                        "<div class='quick-copy-note'>Fast path: copy selected prompt here.</div>",
                        unsafe_allow_html=True,
                    )
                st.caption(prompt["use_case"])
                render_prompt_badges(prompt, max_tags=2)

    if recent_prompts and main_results:
        st.markdown("**Matching prompts**")
    elif recent_prompts and not main_results:
        st.caption("No additional matching prompts outside your recent selections.")

    for prompt in main_results[:MAX_RESULTS]:
        with st.container(border=True):
            selected = current_prompt and prompt["id"] == current_prompt["id"]
            if st.button(
                prompt["title"],
                key=f"select-{prompt['id']}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                handle_result_tap(prompt, current_prompt)
            if selected:
                render_copy_button("Copy selected", prompt["content"], f"quick-main-{prompt['id']}", primary=True)
                st.markdown(
                    "<div class='quick-copy-note'>Fast path: copy selected prompt here.</div>",
                    unsafe_allow_html=True,
                )
            st.caption(prompt["use_case"])
            render_prompt_badges(prompt, max_tags=2)


def render_prompt_detail(prompt: dict | None) -> None:
    st.markdown("### Preview")
    if not prompt:
        st.info("Select a prompt to inspect it here.")
        return

    sync_working_copy(prompt)

    st.markdown(f"## {prompt['title']}")
    st.caption(prompt["use_case"])

    action_left, action_right = st.columns(2, gap="small")
    with action_left:
        render_copy_button("Copy original", prompt["content"], f"original-{prompt['id']}", primary=True)
    with action_right:
        if st.button("Customize copy", use_container_width=True):
            st.session_state["edit_mode"] = True
            sync_working_copy(prompt)
            st.rerun()

    st.markdown(
        "<div class='inline-note'>Source prompt is read-only. Use <strong>Copy original</strong> for the canonical text. "
        "Open <strong>Customize copy</strong> only when you intentionally want a temporary edited draft.</div>",
        unsafe_allow_html=True,
    )

    render_canonical_preview(prompt["content"])
    st.markdown("<div class='copy-footer-note'>Canonical text above stays unchanged.</div>", unsafe_allow_html=True)

    with st.expander("Prompt details", expanded=False):
        render_prompt_badges(prompt)
        meta_left, meta_right = st.columns(2)
        with meta_left:
            st.markdown(f"**Last updated**: {prompt['last_updated']}")
            st.markdown(f"**Source section**: {prompt['source_title']}")
        with meta_right:
            st.markdown(f"**Prompt ID**: `{prompt['id']}`")
            st.markdown(f"**Aliases**: {', '.join(prompt['aliases']) if prompt['aliases'] else 'None'}")
        if prompt["variables"]:
            render_variable_callout(prompt["variables"])

    if st.session_state["edit_mode"]:
        st.divider()
        st.markdown("### Working copy")
        st.markdown(
            "<div class='draft-note'>Temporary working copy. This edited version is separate from the canonical source prompt.</div>",
            unsafe_allow_html=True,
        )
        st.text_area(
            "Edited prompt",
            key="working_copy_text",
            height=360,
            help="This draft resets when you switch prompts and choose to discard changes.",
        )

        edit_left, edit_mid, edit_right = st.columns(3, gap="small")
        with edit_left:
            render_copy_button(
                "Copy edited version",
                st.session_state["working_copy_text"],
                f"edited-{prompt['id']}",
                primary=False,
            )
        with edit_mid:
            if st.button("Reset to original", use_container_width=True):
                st.session_state["working_copy_text"] = prompt["content"]
                st.rerun()
        with edit_right:
            if st.button("Cancel editing", use_container_width=True):
                st.session_state["edit_mode"] = False
                st.session_state["working_copy_text"] = prompt["content"]
                st.rerun()

        if working_copy_is_dirty(prompt):
            st.caption("Working copy has unsaved changes relative to the source prompt.")


@st.cache_data(show_spinner=False)
def cached_load_prompts(base_dir: str) -> tuple[list[dict], dict]:
    return load_prompts(Path(base_dir))


def main() -> None:
    st.set_page_config(page_title="Prompt Library", layout="wide")
    inject_styles()
    ensure_state()

    prompts, source_status = cached_load_prompts(str(BASE_DIR))

    if render_header_controls(prompts, source_status):
        rebuild_prompt_json(BASE_DIR)
        cached_load_prompts.clear()
        st.rerun()

    filtered_prompts = filter_prompts(
        prompts,
        category=st.session_state["category_filter"],
        statuses=st.session_state["status_filter"],
        favorites_only=st.session_state["favorites_only"],
        pinned_only=st.session_state["pinned_only"],
    )
    ranked_prompts = search_prompts(
        filtered_prompts,
        query=st.session_state["query"],
        recent_prompt_ids=st.session_state["recent_prompt_ids"],
    )
    prompts_by_id = {prompt["id"]: prompt for prompt in prompts}
    current_prompt = resolve_selected_prompt(ranked_prompts, st.session_state["selected_prompt_id"])

    render_pending_switch(prompts_by_id)
    if st.session_state.get("auto_copy_feedback"):
        st.warning(st.session_state["auto_copy_feedback"])

    left_col, right_col = st.columns([0.95, 1.35], gap="large")
    with left_col:
        with st.container(height=get_results_panel_height(len(ranked_prompts))):
            render_results(ranked_prompts, current_prompt)
    with right_col:
        render_prompt_detail(current_prompt)


if __name__ == "__main__":
    main()
