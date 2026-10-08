#!/usr/bin/env python3
"""
Script to synchronize all Markdown (.md) files with their JSON counterparts.
Generates structured Markdown files for each quiz JSON file.
"""

import os
import glob
import json

def generate_markdown(json_filepath):
    with open(json_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    title = meta.get("title", "Bibel-Quiz")
    subtitle = meta.get("subtitle", "")
    author = meta.get("author", "Schlachter 1951")
    version = meta.get("version", "2.0.0")
    questions = data.get("questions", [])

    md_lines = []
    md_lines.append(f"# {title}")
    if subtitle:
        md_lines.append(f"*{subtitle}*\n")
    md_lines.append(f"- **Autor:** {author}")
    md_lines.append(f"- **Version:** {version}")
    md_lines.append(f"- **Fragenanzahl:** {len(questions)}\n")
    md_lines.append("---\n")

    for idx, q in enumerate(questions, 1):
        q_id = q.get("questionId", f"q-{idx}")
        q_text = q.get("text", "")
        options = q.get("options", [])
        correct_answers = q.get("correctAnswers", [])
        ref = q.get("bibleReference", "")
        explanation = q.get("explanation", "")

        md_lines.append(f"### Frage {idx} ({q_id})")
        md_lines.append(f"**{q_text}**\n")

        for opt_idx, opt in enumerate(options):
            is_correct = opt_idx in correct_answers
            mark = "✓" if is_correct else " "
            if isinstance(opt, dict):
                opt_str = opt.get("text", "")
            else:
                opt_str = str(opt)
            md_lines.append(f"- [{mark}] {opt_str}")

        md_lines.append(f"\n**Bibelstelle:** {ref}")
        if explanation:
            md_lines.append(f"**Erklärung:** {explanation}")
        md_lines.append("\n---\n")

    return "\n".join(md_lines)

def sync_all_md():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_files = sorted(glob.glob(os.path.join(root_dir, "*.json")))
    quiz_files = [f for f in json_files if os.path.basename(f) != "catalog.json"]

    count = 0
    for json_path in quiz_files:
        md_path = os.path.splitext(json_path)[0] + ".md"
        md_content = generate_markdown(json_path)
        with open(md_path, "w", encoding="utf-8") as mdf:
            mdf.write(md_content)
        count += 1

    print(f"Synchronized {count} Markdown files.")

if __name__ == "__main__":
    sync_all_md()
