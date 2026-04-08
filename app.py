from __future__ import annotations

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
        .app-subtle {
            color: #5b6475;
            font-size: 0.92rem;
        }
        .prompt-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin: 0.35rem 0 0.5rem;
        }
        .prompt-chip {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            background: #eef2ff;
            color: #233876;
            font-size: 0.78rem;
            line-height: 1.2;
            border: 1px solid #dbe4ff;
        }
        .prompt-chip.status-deprecated {
            background: #fff1f2;
            color: #9f1239;
            border-color: #fecdd3;
        }
        .prompt-chip.status-draft {
            background: #fff7ed;
            color: #9a3412;
            border-color: #fed7aa;
        }
        .helper-box {
            border: 1px solid #e2e8f0;
            border-radius: 0.85rem;
            padding: 0.9rem 1rem;
            background: #f8fafc;
            margin-bottom: 1rem;
        }
        .copy-label {
            font-size: 0.86rem;
            color: #5b6475;
            margin-bottom: 0.25rem;
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


def request_prompt_switch(target_prompt: dict, current_prompt: dict | None) -> None:
    if current_prompt and target_prompt["id"] == current_prompt["id"]:
        return

    if current_prompt and st.session_state["edit_mode"] and working_copy_is_dirty(current_prompt):
        st.session_state["pending_prompt_id"] = target_prompt["id"]
        return

    st.session_state["selected_prompt_id"] = target_prompt["id"]
    st.session_state["pending_prompt_id"] = None
    sync_working_copy(target_prompt, force_reset=True)
    remember_recent(target_prompt["id"])


def render_copy_button(label: str, text: str, key: str) -> None:
    button_label = json.dumps(label)
    payload = json.dumps(text)
    components.html(
        f"""
        <div class="copy-label">Clipboard action</div>
        <button id="copy-button-{key}" style="
            width: 100%;
            padding: 0.65rem 0.9rem;
            border: none;
            border-radius: 0.7rem;
            background: #1d4ed8;
            color: white;
            font-weight: 600;
            cursor: pointer;">
            {label}
        </button>
        <script>
        const button = document.getElementById("copy-button-{key}");
        const originalLabel = {button_label};
        const payload = {payload};

        button.addEventListener("click", async () => {{
            try {{
                await navigator.clipboard.writeText(payload);
                button.textContent = "Copied";
                button.style.background = "#047857";
            }} catch (error) {{
                button.textContent = "Clipboard blocked - press Ctrl+C after selecting text";
                button.style.background = "#b45309";
            }}

            setTimeout(() => {{
                button.textContent = originalLabel;
                button.style.background = "#1d4ed8";
            }}, 1800);
        }});
        </script>
        """,
        height=72,
    )


def render_prompt_badges(prompt: dict) -> None:
    tags = "".join(f'<span class="prompt-chip">{tag}</span>' for tag in prompt["tags"][:4])
    status_class = f'prompt-chip status-{prompt["status"]}'
    st.markdown(
        f"""
        <div class="prompt-meta">
            <span class="prompt-chip">{prompt["category"]}</span>
            <span class="{status_class}">{prompt["status"].title()}</span>
            {tags}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(prompts: list[dict], source_status: dict) -> bool:
    with st.sidebar:
        st.title("Prompt Library")
        st.caption("Find the right prompt fast, verify it, then copy the correct version.")

        st.text_input(
            "Search",
            key="query",
            placeholder="debugging traceback, cold outreach, tax risk",
        )

        categories = ["All", *sorted({prompt["category"] for prompt in prompts})]
        current_category = st.session_state["category_filter"]
        category_index = categories.index(current_category) if current_category in categories else 0
        st.session_state["category_filter"] = st.selectbox("Category", categories, index=category_index)

        available_statuses = sorted({prompt["status"] for prompt in prompts})
        selected_statuses = st.multiselect(
            "Status",
            available_statuses,
            default=st.session_state["status_filter"] or available_statuses,
        )
        st.session_state["status_filter"] = selected_statuses or available_statuses
        st.session_state["favorites_only"] = st.checkbox("Favorites only", value=st.session_state["favorites_only"])
        st.session_state["pinned_only"] = st.checkbox("Pinned only", value=st.session_state["pinned_only"])

        st.divider()
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

    return rebuild_clicked


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
    st.subheader("Results")
    if not results:
        st.info("No prompts matched the current search and filters.")
        return

    st.caption(f"{len(results)} prompt(s) matched.")

    recent_lookup = {item for item in st.session_state["recent_prompt_ids"]}
    if not st.session_state["query"] and recent_lookup:
        recent_prompts = [prompt for prompt in results if prompt["id"] in recent_lookup][:4]
        if recent_prompts:
            st.markdown("**Recent**")
            for prompt in recent_prompts:
                with st.container(border=True):
                    selected = current_prompt and prompt["id"] == current_prompt["id"]
                    if st.button(
                        prompt["title"],
                        key=f"recent-{prompt['id']}",
                        type="primary" if selected else "secondary",
                        use_container_width=True,
                    ):
                        request_prompt_switch(prompt, current_prompt)
                        st.rerun()
                    st.caption(prompt["use_case"])
            st.markdown("**All matching prompts**")

    for prompt in results[:MAX_RESULTS]:
        with st.container(border=True):
            selected = current_prompt and prompt["id"] == current_prompt["id"]
            if st.button(
                prompt["title"],
                key=f"select-{prompt['id']}",
                type="primary" if selected else "secondary",
                use_container_width=True,
            ):
                request_prompt_switch(prompt, current_prompt)
                st.rerun()
            st.caption(prompt["use_case"])
            render_prompt_badges(prompt)
            st.markdown(f"<div class='app-subtle'>{prompt['description']}</div>", unsafe_allow_html=True)


def render_prompt_detail(prompt: dict | None) -> None:
    st.subheader("Preview")
    if not prompt:
        st.info("Select a prompt to inspect it here.")
        return

    sync_working_copy(prompt)

    st.markdown(f"## {prompt['title']}")
    st.caption(prompt["use_case"])
    render_prompt_badges(prompt)

    meta_left, meta_right = st.columns(2)
    with meta_left:
        st.markdown(f"**Last updated**: {prompt['last_updated']}")
        st.markdown(f"**Source section**: {prompt['source_title']}")
    with meta_right:
        st.markdown(f"**Prompt ID**: `{prompt['id']}`")
        st.markdown(f"**Aliases**: {', '.join(prompt['aliases']) if prompt['aliases'] else 'None'}")

    if prompt["variables"]:
        st.markdown("**Required inputs / placeholders**")
        for variable in prompt["variables"]:
            st.write(f"- {variable}")

    st.text_area(
        "Canonical prompt",
        value=prompt["content"],
        height=430,
        disabled=True,
        help="This is the source prompt. Copying from here always uses the unmodified version.",
    )

    copy_left, action_right = st.columns([1.1, 0.9])
    with copy_left:
        render_copy_button("Copy original", prompt["content"], f"original-{prompt['id']}")
    with action_right:
        st.markdown(
            "<div class='helper-box'><strong>Safe copy flow</strong><br>"
            "Use the original-copy button for the source prompt. Open Customize copy "
            "only when you intentionally want a temporary edited version.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Customize copy", use_container_width=True):
            st.session_state["edit_mode"] = True
            sync_working_copy(prompt)
            st.rerun()

    if st.session_state["edit_mode"]:
        st.divider()
        st.markdown("### Working copy")
        st.warning("This edited text is temporary and separate from the canonical source prompt.")
        st.text_area(
            "Edited prompt",
            key="working_copy_text",
            height=360,
            help="This draft resets when you switch prompts and choose to discard changes.",
        )

        edit_left, edit_mid, edit_right = st.columns(3)
        with edit_left:
            render_copy_button(
                "Copy edited version",
                st.session_state["working_copy_text"],
                f"edited-{prompt['id']}",
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

    if render_sidebar(prompts, source_status):
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
    current_prompt = resolve_selected_prompt(ranked_prompts, st.session_state["selected_prompt_id"])
    prompts_by_id = {prompt["id"]: prompt for prompt in prompts}

    st.title("Prompt Retrieval and Copy App")
    st.caption(
        "Task-first search, clean source-vs-working-copy separation, and a dataset generated "
        "from your Prompts.docx."
    )
    render_pending_switch(prompts_by_id)

    left_col, right_col = st.columns([0.95, 1.35], gap="large")
    with left_col:
        render_results(ranked_prompts, current_prompt)
    with right_col:
        render_prompt_detail(current_prompt)


if __name__ == "__main__":
    main()
