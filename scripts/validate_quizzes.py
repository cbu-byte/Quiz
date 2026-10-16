#!/usr/bin/env python3
"""
validate_quizzes.py - Validate quiz integrity, catalog consistency, and Markdown synchronization.
"""

import json
import glob
import os
import re
import sys

from sync_all_md import generate_markdown

EXPECTED_CATEGORIES = {
    range(1, 6): "gesetz",
    range(6, 18): "geschichte",
    range(18, 23): "weisheit",
    range(23, 40): "propheten",
    range(40, 67): "nt"
}

def get_expected_category(book_num):
    for r, cat in EXPECTED_CATEGORIES.items():
        if book_num in r:
            return cat
    return None

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    json_files = sorted([
        f for f in glob.glob(os.path.join(root_dir, '*.json'))
        if not f.endswith('catalog.json') and not f.endswith('1_mose_300_fragen_komplett.json')
    ])

    catalog_path = os.path.join(root_dir, 'catalog.json')
    if not os.path.exists(catalog_path):
        print("ERROR: catalog.json not found!")
        sys.exit(1)

    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)

    cat_quizzes = catalog_data.get('quizzes', [])
    cat_urls = {q['downloadUrl']: q for q in cat_quizzes}

    crit_errors = []
    inconsistencies = []
    quality_warnings = []

    all_q_ids = {}

    print(f"Checking {len(json_files)} quiz JSON files against catalog ({len(cat_quizzes)} entries)...")

    for file_path in json_files:
        filename = os.path.basename(file_path)
        rel_url = f"./{filename}"

        if rel_url not in cat_urls:
            inconsistencies.append(f"{filename}: File missing from catalog downloadUrls ({rel_url})")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            crit_errors.append(f"{filename}: Failed to parse JSON: {e}")
            continue

        meta = data.get('metadata', {})
        questions = data.get('questions', [])

        # Metadata required fields check
        req_meta = ['quizId', 'title', 'subtitle', 'author', 'version', 'category', 'difficulty', 'tags', 'questionCount', 'canonicalBookNumber', 'testament']
        for rm in req_meta:
            if rm not in meta or meta[rm] is None or meta[rm] == '':
                inconsistencies.append(f"{filename}: Missing or empty metadata field '{rm}'")

        book_num = meta.get('canonicalBookNumber')
        if not isinstance(book_num, int) or book_num < 1 or book_num > 66:
            crit_errors.append(f"{filename}: Invalid canonicalBookNumber ({book_num})")

        expected_testament = "AT" if (book_num and book_num <= 39) else "NT"
        if meta.get('testament') != expected_testament:
            inconsistencies.append(f"{filename}: Invalid testament '{meta.get('testament')}' (expected '{expected_testament}')")

        expected_cat = get_expected_category(book_num) if book_num else None
        if expected_cat and meta.get('category') != expected_cat:
            inconsistencies.append(f"{filename}: Category mismatch '{meta.get('category')}' (expected '{expected_cat}')")

        if meta.get('questionCount') != len(questions):
            inconsistencies.append(f"{filename}: metadata.questionCount ({meta.get('questionCount')}) != actual questions ({len(questions)})")

        # Catalog entry check
        if rel_url in cat_urls:
            cq = cat_urls[rel_url]
            if cq.get('questionCount') != len(questions):
                inconsistencies.append(f"{filename}: Catalog questionCount ({cq.get('questionCount')}) != actual questions ({len(questions)})")
            if cq.get('quizId') != meta.get('quizId'):
                inconsistencies.append(f"{filename}: Catalog quizId ('{cq.get('quizId')}') != metadata.quizId ('{meta.get('quizId')}')")
            if cq.get('category') != meta.get('category'):
                inconsistencies.append(f"{filename}: Catalog category ('{cq.get('category')}') != metadata.category ('{meta.get('category')}')")
            real_size = os.path.getsize(file_path)
            if cq.get('sizeBytes') != real_size:
                inconsistencies.append(f"{filename}: Catalog sizeBytes ({cq.get('sizeBytes')}) != actual size ({real_size})")

        # Markdown sync check
        md_path = os.path.splitext(file_path)[0] + '.md'
        if not os.path.exists(md_path):
            inconsistencies.append(f"{filename}: Corresponding Markdown file '{os.path.basename(md_path)}' missing")
        else:
            with open(md_path, 'r', encoding='utf-8') as mdf:
                md_content = mdf.read()
            expected_md = generate_markdown(data)
            if md_content != expected_md:
                inconsistencies.append(f"{filename}: Markdown file '{os.path.basename(md_path)}' is not in sync with JSON source")

        # Question checks
        seen_file_q_ids = set()
        for idx, q in enumerate(questions):
            q_id = q.get('questionId')
            if not q_id:
                crit_errors.append(f"{filename} Q#{idx+1}: Missing questionId")
            else:
                if q_id in seen_file_q_ids:
                    inconsistencies.append(f"{filename} Q#{idx+1}: Duplicate questionId '{q_id}' within file")
                seen_file_q_ids.add(q_id)

                if q_id in all_q_ids:
                    inconsistencies.append(f"Duplicate questionId '{q_id}' across files: {filename} and {all_q_ids[q_id]}")
                else:
                    all_q_ids[q_id] = filename

            for req_field in ['questionId', 'text', 'type', 'options', 'correctAnswers', 'bibleReference', 'explanation']:
                if req_field not in q or q[req_field] is None or q[req_field] == '':
                    crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): Missing/empty required field '{req_field}'")

            if q.get('type') not in ['single_choice', 'multiple_choice', 'ordering']:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): Unknown question type '{q.get('type')}'")

            options = q.get('options', [])
            correct = q.get('correctAnswers', [])

            if len(options) < 2:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): Options count ({len(options)}) < 2")

            if not correct:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): correctAnswers is empty")

            qtype = q.get('type')
            if qtype == 'single_choice' and len(correct) != 1:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): single_choice needs exactly 1 correct answer")
            if qtype == 'multiple_choice' and not (2 <= len(correct) < len(options)):
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): multiple_choice needs 2..n-1 correct answers")
            if qtype == 'ordering' and sorted(correct) != list(range(len(options))):
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): ordering must list every option exactly once (correctAnswers = right sequence)")

            for c in correct:
                if not isinstance(c, int) or c < 0 or c >= len(options):
                    crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): correctAnswers index {c} out of bounds (options len: {len(options)})")

            for o_idx, opt in enumerate(options):
                if 'text' not in opt or opt['text'] is None or opt['text'] == '':
                    crit_errors.append(f"{filename} Q#{idx+1} ({q_id}) Opt#{o_idx+1}: Missing option text")
                if 'explanation' not in opt or opt['explanation'] is None:
                    quality_warnings.append(f"{filename} Q#{idx+1} ({q_id}) Opt#{o_idx+1}: Missing option explanation")

            q_text = q.get('text', '')
            if '\ufffd' in q_text:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): Replacement character found in text: {q_text}")
            if '<' in q_text and '>' in q_text and not re.search(r'<\/?(b|i|u|span|p)>', q_text):
                quality_warnings.append(f"{filename} Q#{idx+1} ({q_id}): Potential HTML tag in text: {q_text}")

            # Ref tags syntax check in question text, option texts/explanations, and question explanation
            full_q_str = json.dumps(q, ensure_ascii=False)
            unclosed_refs = re.findall(r'\[ref:[^\]\"\n]*(?:[\"\n]|$)', full_q_str)
            for u in unclosed_refs:
                if not u.rstrip().endswith(']'):
                    crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): Unclosed [ref:] tag: {u!r}")

    print("\n================ VALIDATION REPORT ================")
    print(f"🔴 Critical Errors:   {len(crit_errors)}")
    for e in crit_errors:
        print(f"  - {e}")

    print(f"🟡 Inconsistencies:   {len(inconsistencies)}")
    for e in inconsistencies[:30]:
        print(f"  - {e}")
    if len(inconsistencies) > 30:
        print(f"  ... and {len(inconsistencies) - 30} more inconsistencies")

    print(f"🟢 Quality Warnings:  {len(quality_warnings)}")
    for e in quality_warnings[:15]:
        print(f"  - {e}")
    if len(quality_warnings) > 15:
        print(f"  ... and {len(quality_warnings) - 15} more warnings")

    print("===================================================\n")

    if crit_errors or inconsistencies:
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
