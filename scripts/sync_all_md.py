import json
import os
import glob

def markdown_for_quiz(data):
    meta = data.get("metadata", {})
    questions = data.get("questions", [])

    lines = []
    lines.append(f"# {meta.get('title', '')}")
    if meta.get("subtitle"):
        lines.append(f"\n*{meta.get('subtitle')}*\n")
    lines.append(f"- **Autor:** {meta.get('author', 'Schlachter 1951')}")
    lines.append(f"- **Version:** {meta.get('version', '2.0.0')}")
    lines.append(f"- **Fragen:** {len(questions)}")
    lines.append("\n---\n")

    for idx, q in enumerate(questions, 1):
        q_id = q.get("questionId", f"q-{idx}")
        text = q.get("text", "")
        options = q.get("options", [])
        correct = set(q.get("correctAnswers", []))
        ref = q.get("bibleReference", "")
        explanation = q.get("explanation", "")

        lines.append(f"### Frage {idx} ({q_id})")
        lines.append(f"**{text}**\n")

        for opt_idx, opt in enumerate(options):
            opt_text = opt.get("text", "") if isinstance(opt, dict) else str(opt)
            is_correct = " [RICHTIG]" if opt_idx in correct else ""
            lines.append(f"- [{ 'x' if opt_idx in correct else ' ' }] {opt_text}{is_correct}")

        if ref:
            lines.append(f"\n*Bibelstelle:* {ref}")
        if explanation:
            lines.append(f"*Erklärung:* {explanation}")
        lines.append("\n---\n")

    return "\n".join(lines)

def sync_all_md():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_files = glob.glob(os.path.join(root_dir, "*.json"))
    json_files = [f for f in json_files if not f.endswith("catalog.json")]

    for filepath in sorted(json_files):
        md_filepath = filepath.replace(".json", ".md")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        md_content = markdown_for_quiz(data)
        with open(md_filepath, "w", encoding="utf-8") as mdf:
            mdf.write(md_content)

    print(f"Erfolgreich {len(json_files)} Markdown-Dateien aus JSON synchronisiert.")

if __name__ == "__main__":
    sync_all_md()
