#!/usr/bin/env python3
"""
validate_quizzes.py - Validate quiz integrity, catalog consistency, and markdown sync.
"""

import json
import glob
import os
import re
import sys

# Expected canonical book mapping (1..66)
EXPECTED_BOOKS = {
    1: ("01_1_mose.json", "AT", "at"),
    2: ("02_2_mose.json", "AT", "gesetz"),
    3: ("03_3_mose.json", "AT", "gesetz"),
    4: ("04_4_mose.json", "AT", "gesetz"),
    5: ("05_5_mose.json", "AT", "gesetz"),
    6: ("06_josua.json", "AT", "geschichte"),
    7: ("07_richter.json", "AT", "geschichte"),
    8: ("08_rut.json", "AT", "geschichte"),
    9: ("09_1_samuel.json", "AT", "geschichte"),
    10: ("10_2_samuel.json", "AT", "geschichte"),
    11: ("11_1_koenige.json", "AT", "geschichte"),
    12: ("12_2_koenige.json", "AT", "geschichte"),
    13: ("13_1_chronik.json", "AT", "geschichte"),
    14: ("14_2_chronik.json", "AT", "geschichte"),
    15: ("15_esra.json", "AT", "geschichte"),
    16: ("16_nehemia.json", "AT", "geschichte"),
    17: ("17_esther.json", "AT", "geschichte"),
    18: ("18_hiob.json", "AT", "weisheit"),
    19: ("19_psalmen.json", "AT", "weisheit"),
    20: ("20_sprueche.json", "AT", "weisheit"),
    21: ("21_prediger.json", "AT", "weisheit"),
    22: ("22_hohelied.json", "AT", "weisheit"),
    23: ("23_jesaja.json", "AT", "propheten"),
    24: ("24_jeremia.json", "AT", "propheten"),
    25: ("25_klagelieder.json", "AT", "propheten"),
    26: ("26_hesekiel.json", "AT", "propheten"),
    27: ("27_daniel.json", "AT", "propheten"),
    28: ("28_hosea.json", "AT", "propheten"),
    29: ("29_joel.json", "AT", "propheten"),
    30: ("30_amos.json", "AT", "propheten"),
    31: ("31_obadja.json", "AT", "propheten"),
    32: ("32_jona.json", "AT", "propheten"),
    33: ("33_micha.json", "AT", "propheten"),
    34: ("34_nahum.json", "AT", "propheten"),
    35: ("35_habakuk.json", "AT", "propheten"),
    36: ("36_zephanja.json", "AT", "propheten"),
    37: ("37_haggai.json", "AT", "propheten"),
    38: ("38_sacharja.json", "AT", "propheten"),
    39: ("39_maleachi.json", "AT", "propheten"),
    40: ("40_matthaeus.json", "NT", "nt"),
    41: ("41_markus.json", "NT", "nt"),
    42: ("42_lukas.json", "NT", "nt"),
    43: ("43_johannes.json", "NT", "nt"),
    44: ("44_apostelgeschichte.json", "NT", "nt"),
    45: ("45_roemer.json", "NT", "nt"),
    46: ("46_1_korinther.json", "NT", "nt"),
    47: ("47_2_korinther.json", "NT", "nt"),
    48: ("48_galater.json", "NT", "nt"),
    49: ("49_epheser.json", "NT", "nt"),
    50: ("50_philipper.json", "NT", "nt"),
    51: ("51_kolosser.json", "NT", "nt"),
    52: ("52_1_thessalonicher.json", "NT", "nt"),
    53: ("53_2_thessalonicher.json", "NT", "nt"),
    54: ("54_1_timotheus.json", "NT", "nt"),
    55: ("55_2_timotheus.json", "NT", "nt"),
    56: ("56_titus.json", "NT", "nt"),
    57: ("57_philemon.json", "NT", "nt"),
    58: ("58_hebraeer.json", "NT", "nt"),
    59: ("59_jakobus.json", "NT", "nt"),
    60: ("60_1_petrus.json", "NT", "nt"),
    61: ("61_2_petrus.json", "NT", "nt"),
    62: ("62_1_johannes.json", "NT", "nt"),
    63: ("63_2_johannes.json", "NT", "nt"),
    64: ("64_3_johannes.json", "NT", "nt"),
    65: ("65_judas.json", "NT", "nt"),
    66: ("66_offenbarung.json", "NT", "nt")
}

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

        # Metadata checks
        req_meta = ['quizId', 'title', 'subtitle', 'author', 'version', 'category', 'difficulty', 'tags', 'questionCount', 'canonicalBookNumber', 'testament']
        for rm in req_meta:
            if rm not in meta or meta[rm] is None or meta[rm] == '':
                inconsistencies.append(f"{filename}: Missing or empty metadata field '{rm}'")

        book_num = meta.get('canonicalBookNumber')
        if book_num in EXPECTED_BOOKS:
            exp_filename, exp_testament, exp_category = EXPECTED_BOOKS[book_num]
            if filename != exp_filename:
                inconsistencies.append(f"{filename}: Filename mismatch for book #{book_num} (expected {exp_filename})")
            if meta.get('testament') != exp_testament:
                inconsistencies.append(f"{filename}: Testament mismatch (expected {exp_testament}, got {meta.get('testament')})")
            if meta.get('category') != exp_category:
                inconsistencies.append(f"{filename}: Category mismatch (expected {exp_category}, got {meta.get('category')})")
        else:
            inconsistencies.append(f"{filename}: Invalid canonicalBookNumber '{book_num}'")

        if meta.get('questionCount') != len(questions):
            inconsistencies.append(f"{filename}: metadata.questionCount ({meta.get('questionCount')}) != actual questions ({len(questions)})")

        # Catalog entry check
        if rel_url in cat_urls:
            cq = cat_urls[rel_url]
            if cq.get('questionCount') != len(questions):
                inconsistencies.append(f"{filename}: Catalog questionCount ({cq.get('questionCount')}) != actual questions ({len(questions)})")
            if cq.get('quizId') != meta.get('quizId'):
                inconsistencies.append(f"{filename}: Catalog quizId ('{cq.get('quizId')}') != metadata.quizId ('{meta.get('quizId')}')")
            real_size = os.path.getsize(file_path)
            if cq.get('sizeBytes') != real_size:
                inconsistencies.append(f"{filename}: Catalog sizeBytes ({cq.get('sizeBytes')}) != actual size ({real_size})")

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

            for req_field in ['questionId', 'text', 'type', 'options', 'correctAnswers', 'bibleReference', 'explanation', 'explanationReviewed']:
                if req_field not in q or q[req_field] is None:
                    crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): Missing required field '{req_field}'")

            if q.get('type') not in ['single_choice', 'multiple_choice', 'ordering']:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): Unknown question type '{q.get('type')}'")

            options = q.get('options', [])
            correct = q.get('correctAnswers', [])

            if len(options) < 2:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): Options count ({len(options)}) < 2")

            if not isinstance(correct, list) or len(correct) == 0:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): correctAnswers is empty or not a list")

            qtype = q.get('type')
            if qtype == 'single_choice' and len(correct) != 1:
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): single_choice needs exactly 1 correct answer (got {len(correct)})")
            if qtype == 'multiple_choice' and not (2 <= len(correct) < len(options)):
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): multiple_choice needs 2..n-1 correct answers (got {len(correct)} for {len(options)} options)")
            if qtype == 'ordering' and sorted(correct) != list(range(len(options))):
                crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): ordering must list every option index exactly once")

            for c in correct:
                if not isinstance(c, int) or c < 0 or c >= len(options):
                    crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): correctAnswers index {c} out of bounds (options len: {len(options)})")

            for o_idx, opt in enumerate(options):
                if 'text' not in opt or opt['text'] is None or opt['text'] == '':
                    crit_errors.append(f"{filename} Q#{idx+1} ({q_id}) Opt#{o_idx+1}: Missing option text")
                if 'explanation' not in opt or opt['explanation'] is None:
                    quality_warnings.append(f"{filename} Q#{idx+1} ({q_id}) Opt#{o_idx+1}: Missing option explanation")

            # Syntax and format checks
            texts_to_check = [q.get('text', ''), q.get('explanation', ''), q.get('bibleReference', '')]
            for opt in options:
                texts_to_check.append(opt.get('text', ''))
                texts_to_check.append(opt.get('explanation', ''))

            for text in texts_to_check:
                if '\ufffd' in text:
                    crit_errors.append(f"{filename} Q#{idx+1} ({q_id}): UTF-8 replacement character found: {text}")
                # Check for malformed [ref:] tags
                open_refs = len(re.findall(r'\[ref:', text))
                close_refs = len(re.findall(r'\[ref:[^\]]+\]', text))
                if open_refs != close_refs:
                    inconsistencies.append(f"{filename} Q#{idx+1} ({q_id}): Unclosed or malformed [ref:] tag in text: {text}")
                # Check for unexpected HTML tags
                if '<' in text and '>' in text and not re.search(r'<\/?(b|i|u|span|p)>', text):
                    quality_warnings.append(f"{filename} Q#{idx+1} ({q_id}): Potential HTML tag in text: {text}")

        # Check Markdown synchronization
        md_path = os.path.splitext(file_path)[0] + '.md'
        if not os.path.exists(md_path):
            inconsistencies.append(f"{filename}: Corresponding Markdown file '{os.path.basename(md_path)}' missing")
        else:
            expected_md = generate_markdown(data)
            try:
                with open(md_path, 'r', encoding='utf-8') as mdf:
                    actual_md = mdf.read()
                if actual_md.strip() != expected_md.strip():
                    inconsistencies.append(f"{filename}: Markdown file '{os.path.basename(md_path)}' out of sync with JSON")
            except Exception as e:
                inconsistencies.append(f"{filename}: Failed to read Markdown file: {e}")

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
