#!/usr/bin/env python3
"""
sync_all_md.py - Synchronize all Markdown files from JSON quiz data.
"""

import json
import glob
import os
import sys

def generate_markdown(data):
    meta = data.get('metadata', {})
    questions = data.get('questions', [])

    title = meta.get('title', '')
    quiz_id = meta.get('quizId', '')
    category = meta.get('category', '')
    difficulty = meta.get('difficulty', '')
    subtitle = meta.get('subtitle', '')
    tags = ", ".join(meta.get('tags', []))

    md_lines = []
    md_lines.append(f"# {title}\n")
    md_lines.append(f"**Quiz-ID:** `{quiz_id}`  ")
    md_lines.append(f"**Kategorie:** `{category}` | **Schwierigkeit:** `{difficulty}`  ")
    md_lines.append(f"**Untertitel:** {subtitle}  ")
    md_lines.append(f"**Tags:** {tags}  \n")
    md_lines.append("---\n")

    for idx, q in enumerate(questions, start=1):
        q_text = q.get('text', '')
        md_lines.append(f"### {idx}. {q_text}\n")

        options = q.get('options', [])
        correct_answers = q.get('correctAnswers', [])

        for o_idx, opt in enumerate(options):
            check_mark = "x" if o_idx in correct_answers else " "
            opt_text = opt.get('text', '')
            opt_exp = opt.get('explanation', '')

            if opt_exp:
                md_lines.append(f"- [{check_mark}] {opt_text} | {opt_exp}")
            else:
                md_lines.append(f"- [{check_mark}] {opt_text}")

        md_lines.append("")
        ref = q.get('bibleReference', '')
        exp = q.get('explanation', '')
        md_lines.append(f"**Bibelstelle:** {ref}")
        md_lines.append(f"**Erklärung:** {exp}\n")

    return "\n".join(md_lines)

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    json_files = sorted([
        f for f in glob.glob(os.path.join(root_dir, '*.json'))
        if not f.endswith('catalog.json') and not f.endswith('1_mose_300_fragen_komplett.json')
    ])

    synced_count = 0
    for json_path in json_files:
        md_path = os.path.splitext(json_path)[0] + '.md'

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        md_content = generate_markdown(data)

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        synced_count += 1

    print(f"Successfully synchronized {synced_count} Markdown files from JSON data.")

if __name__ == '__main__':
    main()
