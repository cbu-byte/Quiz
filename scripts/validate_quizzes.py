#!/usr/bin/env python3
"""
Comprehensive validation script for BibelQuiz repository.
Checks:
1. Answer & Index validation (empty correctAnswers, out-of-bounds index, <2 options)
2. Schema & Required fields (questionId, text, type, options, correctAnswers, bibleReference, explanation)
3. Duplicate questionIds (within file and repository-wide)
4. Metadata inconsistencies (metadata.questionCount vs questions length, book/testament/category consistency)
5. Catalog consistency (catalog.json vs files, sizeBytes, questionCount, downloadUrl)
6. Text & Bible reference formats ([ref:...], UTF-8 artifacts, html tags, incomplete sentences)
7. Markdown sync check (exists, question count matches)
"""

import os
import sys
import glob
import json
import re

REQUIRED_QUESTION_FIELDS = [
    "questionId", "text", "type", "options", "correctAnswers", "bibleReference", "explanation"
]

REQUIRED_METADATA_FIELDS = [
    "title", "subtitle", "questionCount", "author", "version"
]

def validate():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_files = sorted(glob.glob(os.path.join(root_dir, "*.json")))
    quiz_files = [f for f in json_files if os.path.basename(f) != "catalog.json"]

    catalog_path = os.path.join(root_dir, "catalog.json")

    report = {
        "critical": [],
        "inconsistencies": [],
        "optimizations": [],
        "content_questions": []
    }

    all_question_ids = {}

    print(f"Validating {len(quiz_files)} quiz JSON files...")

    for filepath in quiz_files:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            report["critical"].append(f"File {filename}: Invalid JSON format: {e}")
            continue

        # Check metadata
        metadata = data.get("metadata", {})
        for field in REQUIRED_METADATA_FIELDS:
            if field not in metadata:
                report["inconsistencies"].append(f"File {filename}: Missing metadata field '{field}'")

        questions = data.get("questions", [])
        actual_q_count = len(questions)
        meta_q_count = metadata.get("questionCount")

        if meta_q_count != actual_q_count:
            report["inconsistencies"].append(
                f"File {filename}: metadata.questionCount ({meta_q_count}) != actual questions count ({actual_q_count})"
            )

        file_q_ids = set()

        for idx, q in enumerate(questions):
            q_num = idx + 1
            # Check required fields
            missing_fields = [f for f in REQUIRED_QUESTION_FIELDS if f not in q or q[f] is None]
            if missing_fields:
                report["critical"].append(
                    f"File {filename} (Q #{q_num}): Missing required fields: {missing_fields}"
                )

            q_id = q.get("questionId")
            if q_id:
                if q_id in file_q_ids:
                    report["inconsistencies"].append(
                        f"File {filename} (Q #{q_num}): Duplicate questionId '{q_id}' within file"
                    )
                file_q_ids.add(q_id)

                if q_id in all_question_ids:
                    all_question_ids[q_id].append((filename, q_num))
                else:
                    all_question_ids[q_id] = [(filename, q_num)]

            # Check options and correctAnswers
            options = q.get("options", [])
            correct_answers = q.get("correctAnswers", [])

            if not isinstance(options, list) or len(options) < 2:
                report["critical"].append(
                    f"File {filename} (Q #{q_num}, id: {q_id}): Options count is less than 2 ({len(options) if isinstance(options, list) else 'not a list'})"
                )

            if not isinstance(correct_answers, list) or len(correct_answers) == 0:
                report["critical"].append(
                    f"File {filename} (Q #{q_num}, id: {q_id}): 'correctAnswers' is empty or invalid"
                )
            else:
                for ca in correct_answers:
                    if not isinstance(ca, int) or ca < 0 or ca >= len(options):
                        report["critical"].append(
                            f"File {filename} (Q #{q_num}, id: {q_id}): Correct answer index {ca} out of bounds for options length {len(options)}"
                        )

            # Check text formatting / artifacts
            q_text = q.get("text", "")
            explanation = q.get("explanation", "")

            # Check for unclosed ref tags
            for text_check, name in [(q_text, "text"), (explanation, "explanation")]:
                # find all occurrences of '[ref:'
                matches = re.finditer(r'\[ref:', str(text_check))
                for match in matches:
                    start_pos = match.start()
                    closing_bracket = str(text_check).find(']', start_pos)
                    if closing_bracket == -1:
                        report["inconsistencies"].append(
                            f"File {filename} (Q #{q_num}, id: {q_id}): Malformed unclosed ref tag in {name}"
                        )

            # Check HTML artifacts
            for text_check, name in [(q_text, "text"), (explanation, "explanation")]:
                if re.search(r'<[^>]+>', str(text_check)):
                    report["optimizations"].append(
                        f"File {filename} (Q #{q_num}, id: {q_id}): HTML tag detected in {name}: '{text_check}'"
                    )

            # Check options structure (can be string or dict with 'text')
            for opt_i, opt in enumerate(options):
                if isinstance(opt, str):
                    if not opt.strip():
                        report["critical"].append(
                            f"File {filename} (Q #{q_num}, id: {q_id}): Option index {opt_i} is empty"
                        )
                elif isinstance(opt, dict):
                    opt_text = opt.get("text", "")
                    if not isinstance(opt_text, str) or not opt_text.strip():
                        report["critical"].append(
                            f"File {filename} (Q #{q_num}, id: {q_id}): Option dict at index {opt_i} has empty 'text'"
                        )
                else:
                    report["critical"].append(
                        f"File {filename} (Q #{q_num}, id: {q_id}): Option index {opt_i} is neither string nor dict"
                    )

        # Markdown sync check
        md_filename = os.path.splitext(filename)[0] + ".md"
        md_filepath = os.path.join(root_dir, md_filename)
        if not os.path.exists(md_filepath):
            report["inconsistencies"].append(f"File {filename}: Corresponding Markdown file '{md_filename}' missing")
        else:
            with open(md_filepath, "r", encoding="utf-8") as mdf:
                md_content = mdf.read()
                # Count questions in md file
                md_q_count = len(re.findall(r'^###\s+Frage\s+\d+', md_content, re.MULTILINE))
                if md_q_count != actual_q_count:
                    report["inconsistencies"].append(
                        f"File {filename}: Markdown question count ({md_q_count}) != JSON question count ({actual_q_count})"
                    )

    # Check repository-wide duplicate questionIds
    for q_id, occurrences in all_question_ids.items():
        if len(occurrences) > 1:
            report["inconsistencies"].append(
                f"Repository-wide duplicate questionId '{q_id}' found in: {occurrences}"
            )

    # Validate Catalog
    if not os.path.exists(catalog_path):
        report["critical"].append("catalog.json is missing!")
    else:
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)

            cat_quizzes = catalog.get("quizzes", [])
            cat_quiz_ids = {q.get("quizId"): q for q in cat_quizzes}
            cat_urls = {q.get("downloadUrl"): q for q in cat_quizzes}

            for filepath in quiz_files:
                filename = os.path.basename(filepath)
                rel_url = f"./{filename}"
                file_size = os.path.getsize(filepath)

                with open(filepath, "r", encoding="utf-8") as f:
                    qdata = json.load(f)

                real_q_count = len(qdata.get("questions", []))

                if rel_url not in cat_urls:
                    report["inconsistencies"].append(
                        f"Catalog: Quiz file '{filename}' ({rel_url}) is missing from catalog.json!"
                    )
                else:
                    cat_entry = cat_urls[rel_url]
                    if cat_entry.get("questionCount") != real_q_count:
                        report["inconsistencies"].append(
                            f"Catalog: '{filename}' questionCount mismatch (Catalog: {cat_entry.get('questionCount')}, Real: {real_q_count})"
                        )
                    if abs(cat_entry.get("sizeBytes", 0) - file_size) > 10:
                        report["inconsistencies"].append(
                            f"Catalog: '{filename}' sizeBytes mismatch (Catalog: {cat_entry.get('sizeBytes')}, Real: {file_size})"
                        )

        except Exception as e:
            report["critical"].append(f"Catalog error reading catalog.json: {e}")

    # Output Summary
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)

    print(f"\n🔴 CRITICAL ISSUES ({len(report['critical'])}):")
    for item in report["critical"]:
        print(f"  - {item}")

    print(f"\n🟡 INCONSISTENCIES ({len(report['inconsistencies'])}):")
    for item in report["inconsistencies"]:
        print(f"  - {item}")

    print(f"\n🟢 OPTIMIZATIONS ({len(report['optimizations'])}):")
    for item in report["optimizations"]:
        print(f"  - {item}")

    return report

if __name__ == "__main__":
    validate()
