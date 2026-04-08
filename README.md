# Prompt Library Streamlit App

This folder contains a complete Streamlit app for browsing, searching, previewing, and copying the prompts stored in `Prompts.docx`.

## What is included

- `app.py` - the Streamlit entrypoint
- `prompt_app/parser.py` - imports prompt content directly from `Prompts.docx`
- `prompt_app/search.py` - weighted lexical search and filters
- `prompt_app/library.py` - prompt loading and JSON rebuild helpers
- `scripts/export_prompts.py` - CLI exporter for regenerating `data/prompts.json`
- `tests/test_prompt_library.py` - basic parser and search checks
- `data/prompts.json` - generated prompt library data

## Run locally

```powershell
pip install -r requirements.txt
streamlit run app.py
```

You can also run:

```powershell
streamlit run streamlit_app.py
```

## Refresh the JSON after editing Prompts.docx

```powershell
python scripts/export_prompts.py --docx Prompts.docx --output data/prompts.json
```

You can also rebuild from inside the Streamlit sidebar using the `Rebuild prompts from DOCX` button.

## Behavior

- Search is weighted toward title, aliases, tags, and use case before body text.
- The canonical prompt is always read-only and has its own dedicated copy button.
- The edited working copy is separate and only appears after you choose `Customize copy`.
- Switching prompts while edits are dirty requires explicit discard confirmation.

## Copy into your repo

Copy this folder structure into the root of your repo, keeping `Prompts.docx` alongside `app.py` unless you plan to maintain only `data/prompts.json`.
