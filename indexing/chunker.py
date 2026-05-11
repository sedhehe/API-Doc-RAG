import re
from pathlib import Path
from config import DOCS_DIR

def slugify(text: str) -> str:
    text = text.lower().strip("#").strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def detect_chunk_type(current_h2: str) -> str:
    endpoint_sections = ["users", "teams", "notifications"]
    if current_h2 and current_h2.lower() in endpoint_sections:
        return "endpoint"
    return "concept"

def parse_metadata_from_path(file_path: Path) -> dict:
    parts = file_path.parts
    version = parts[-2]
    doc_category = parts[-1].replace("-", "_").replace(".md", "")
    return {
        "version": version,
        "source_file": str(file_path),
        "doc_category": doc_category
    }

def chunk_markdown(file_path: Path) -> list[dict]:
    path_meta = parse_metadata_from_path(file_path)
    chunks = []
    current_h2 = None
    current_h3 = None
    prose_lines = []
    code_lines = []
    table_lines = []
    inside_code = False
    doc_title = None

    def save_chunk():
        if not current_h3 or (not prose_lines and not table_lines and not code_lines):
            return

        prose = " ".join(prose_lines).strip()
        code = "\n".join(code_lines).strip()
        table = "\n".join(table_lines).strip()
        h2 = current_h2 or ""
        h3 = current_h3.strip("# ").strip()
        
        content_text = prose if prose else table

        chunk_id = f"{path_meta['version']}-{slugify(h2)}-{slugify(h3)}"

        chunk = {
            "content": f"{current_h3}\n\n{content_text}",
            "metadata": {
                **path_meta,
                "doc_title": doc_title,
                "parent_section": h2,
                "section": h3,
                "chunk_type": detect_chunk_type(h2),
                "code_example": code,
                "parameter_table":table,
                "chunk_id": chunk_id,
                "source_url": f"/docs/{path_meta['version']}/{path_meta['doc_category']}#{slugify(h3)}"
            }
        }
        chunks.append(chunk)

    with open(DOCS_DIR / file_path) as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# ") and not stripped.startswith("##"):
            doc_title = stripped[2:]
            continue

        if stripped.startswith("## "):
            save_chunk()
            prose_lines = []
            code_lines = []
            table_lines = []
            current_h2 = stripped[3:]
            current_h3 = None
            continue

        if stripped.startswith("### "):
            save_chunk()
            prose_lines = []
            code_lines = []
            table_lines = []
            current_h3 = stripped
            continue

        if stripped.startswith("```"):
            inside_code = not inside_code    # ← toggles on/off
            continue

        if stripped.startswith("|"):
            table_lines.append(stripped)
            continue

        if inside_code:
            code_lines.append(stripped)
        elif stripped:
            prose_lines.append(stripped)

    save_chunk()
    return chunks