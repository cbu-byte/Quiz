#!/usr/bin/env python3
"""
sync_all_md.py
Generates / synchronizes Markdown (.md) quiz files from canonical JSON quiz files.
"""

import glob
import json
import os
import sys

def json_to_md(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    questions = data.get("questions", [])

    title = meta.get("title", "Bibel-Quiz")
    quiz_id = meta.get("quizId", "")
    category = meta.get("category", "")
    difficulty = meta.get("difficulty", "medium")
    subtitle = meta.get("subtitle", "")
    tags = ", ".join(meta.get("tags", []))

    lines = []
    lines.append(f"# {title}\n")
    lines.append(f"**Quiz-ID:** `{quiz_id}`  ")
    if category:
        lines.append(f"**Kategorie:** `{category}` | **Schwierigkeit:** `{difficulty}`  ")
    else:
        lines.append(f"**Schwierigkeit:** `{difficulty}`  ")
    if subtitle:
        lines.append(f"**Untertitel:** {subtitle}  ")
    if tags:
        lines.append(f"**Tags:** {tags}  ")

    lines.append("\n---\n")

    for idx, q in enumerate(questions, 1):
        q_text = q.get("text", "").strip()
        lines.append(f"### {idx}. {q_text}\n")

        opts = q.get("options", [])
        correct_indices = set(q.get("correctAnswers", []))

        for o_idx, opt in enumerate(opts):
            opt_text = opt.get("text", "").strip()
            opt_exp = opt.get("explanation", "").strip()
            checkbox = "[x]" if o_idx in correct_indices else "[ ]"
            if opt_exp:
                lines.append(f"- {checkbox} {opt_text} | {opt_exp}")
            else:
                lines.append(f"- {checkbox} {opt_text}")

        lines.append("")
        ref = q.get("bibleReference", "").strip()
        exp = q.get("explanation", "").strip()
        if ref:
            lines.append(f"**Bibelstelle:** {ref}")
        if exp:
            lines.append(f"**Erklärung:** {exp}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"

def sync_all():
    json_files = sorted([f for f in glob.glob("*.json") if f != "catalog.json"])
    synced_count = 0

    for json_path in json_files:
        md_path = json_path.replace(".json", ".md")
        md_content = json_to_md(json_path)

        # Write or update MD file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        synced_count += 1

    print(f"Successfully synchronized {synced_count} Markdown files from JSON sources.")

if __name__ == "__main__":
    sync_all()
