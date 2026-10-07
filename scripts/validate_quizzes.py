#!/usr/bin/env python3
"""
validate_quizzes.py
Comprehensive automated validation script for BibelQuiz repository.
Validates all JSON files, catalog.json, and Markdown sync.
"""

import glob
import json
import os
import re
import sys

REQUIRED_QUESTION_FIELDS = [
    "questionId",
    "text",
    "type",
    "options",
    "correctAnswers",
    "bibleReference",
    "explanation",
]

def validate_all():
    errors_critical = []
    errors_inconsistency = []
    errors_quality = []

    json_files = sorted([f for f in glob.glob("*.json") if f != "catalog.json"])

    if not os.path.exists("catalog.json"):
        errors_critical.append("catalog.json is missing from repository root")
        catalog_data = {}
    else:
        with open("catalog.json", "r", encoding="utf-8") as f:
            try:
                catalog_data = json.load(f)
            except Exception as e:
                errors_critical.append(f"catalog.json is invalid JSON: {e}")
                catalog_data = {}

    cat_quizzes = list(catalog_data.get("quizzes", []))
    for category in catalog_data.get("categories", []):
        if isinstance(category, dict) and "quizzes" in category and isinstance(category["quizzes"], list):
            cat_quizzes.extend(category["quizzes"])

    cat_by_url = {q.get("downloadUrl", "").lstrip("./"): q for q in cat_quizzes if isinstance(q, dict)}
    cat_by_id = {q.get("quizId"): q for q in cat_quizzes if isinstance(q, dict)}

    all_qids = {}

    for fname in json_files:
        file_path = fname
        file_size = os.path.getsize(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            errors_critical.append(f"[{fname}] Invalid JSON syntax: {e}")
            continue

        meta = data.get("metadata", {})
        quiz_id = meta.get("quizId")
        questions = data.get("questions", [])

        # 1. Metadata check
        qc = meta.get("questionCount")
        if qc is None:
            errors_inconsistency.append(f"[{fname}] metadata.questionCount is missing")
        elif qc != len(questions):
            errors_inconsistency.append(
                f"[{fname}] metadata.questionCount ({qc}) != actual questions ({len(questions)})"
            )

        if not meta.get("category"):
            errors_inconsistency.append(f"[{fname}] metadata.category is missing")

        # 2. Catalog check
        cat_entry = cat_by_url.get(fname)
        if not cat_entry:
            errors_inconsistency.append(f"[{fname}] File not referenced in catalog.json downloadUrl")
        else:
            if cat_entry.get("questionCount") != len(questions):
                errors_inconsistency.append(
                    f"[{fname}] catalog.json questionCount ({cat_entry.get('questionCount')}) != actual ({len(questions)})"
                )
            if cat_entry.get("quizId") != quiz_id:
                errors_inconsistency.append(
                    f"[{fname}] catalog.json quizId ({cat_entry.get('quizId')}) != metadata.quizId ({quiz_id})"
                )
            if abs(cat_entry.get("sizeBytes", 0) - file_size) > 5:
                errors_inconsistency.append(
                    f"[{fname}] catalog.json sizeBytes ({cat_entry.get('sizeBytes')}) != actual size ({file_size})"
                )

        # 3. Question validation
        qids_in_file = set()
        for idx, q in enumerate(questions):
            qid = q.get("questionId")

            # Check required fields
            for rf in REQUIRED_QUESTION_FIELDS:
                if rf not in q or q[rf] is None or (isinstance(q[rf], str) and not q[rf].strip()):
                    errors_critical.append(
                        f"[{fname}] Question idx {idx} (ID: {qid}) missing/empty required field '{rf}'"
                    )

            # Answers & Options
            ca = q.get("correctAnswers", [])
            opts = q.get("options", [])

            if not isinstance(ca, list) or len(ca) == 0:
                errors_critical.append(f"[{fname}] Question {qid} correctAnswers is empty or not a list")
            else:
                for a in ca:
                    if not isinstance(a, int) or a < 0 or a >= len(opts):
                        errors_critical.append(
                            f"[{fname}] Question {qid} correctAnswer index {a} out of bounds (options len {len(opts)})"
                        )

            if not isinstance(opts, list) or len(opts) < 2:
                errors_critical.append(f"[{fname}] Question {qid} has fewer than 2 options")
            else:
                for o_idx, opt in enumerate(opts):
                    if not isinstance(opt, dict) or not opt.get("text", "").strip():
                        errors_critical.append(f"[{fname}] Question {qid} option {o_idx} empty or invalid")

            # Duplicate QID inside file
            if qid:
                if qid in qids_in_file:
                    errors_inconsistency.append(f"[{fname}] Duplicate questionId inside file: {qid}")
                qids_in_file.add(qid)

                if qid not in all_qids:
                    all_qids[qid] = []
                all_qids[qid].append(fname)

            # Text artifacts / Reference tags
            text_fields = [
                ("text", q.get("text")),
                ("bibleReference", q.get("bibleReference")),
                ("explanation", q.get("explanation")),
            ]
            if isinstance(opts, list):
                for o_i, o in enumerate(opts):
                    if isinstance(o, dict):
                        text_fields.append((f"option[{o_i}].text", o.get("text")))
                        text_fields.append((f"option[{o_i}].explanation", o.get("explanation")))

            for field_name, tf in text_fields:
                if not isinstance(tf, str):
                    continue
                if re.search(r"<[^>]+>", tf):
                    errors_quality.append(f"[{fname}] Question {qid} field {field_name} contains HTML: {tf}")
                if "[ref:" in tf:
                    starts = len(re.findall(r"\[ref:", tf))
                    ends = len(re.findall(r"\[ref:[^\]]+\]", tf))
                    if starts != ends:
                        errors_quality.append(f"[{fname}] Question {qid} field {field_name} has malformed [ref:] tag")

        # 4. Markdown sync check
        md_name = fname.replace(".json", ".md")
        if not os.path.exists(md_name):
            errors_inconsistency.append(f"[{fname}] Missing corresponding MD file {md_name}")

    print("==================================================")
    print("           BIBELQUIZ VALIDATION REPORT            ")
    print("==================================================")
    print(f"Total Quiz JSON Files Analyzed: {len(json_files)}")
    print(f"Critical Errors (🔴): {len(errors_critical)}")
    print(f"Inconsistencies (🟡): {len(errors_inconsistency)}")
    print(f"Code Quality / Formatting Issues (🟢): {len(errors_quality)}")
    print("--------------------------------------------------")

    if errors_critical:
        print("\n🔴 CRITICAL ERRORS:")
        for e in errors_critical:
            print(f"  - {e}")

    if errors_inconsistency:
        print("\n🟡 INCONSISTENCIES:")
        for e in errors_inconsistency:
            print(f"  - {e}")

    if errors_quality:
        print("\n🟢 QUALITY ISSUES:")
        for e in errors_quality:
            print(f"  - {e}")

    if not errors_critical and not errors_inconsistency and not errors_quality:
        print("\n✅ ALL VALIDATIONS PASSED PERFECTLY WITH 0 ERRORS!")
        return 0
    elif not errors_critical and not errors_inconsistency:
        print("\n✅ NO CRITICAL OR INCONSISTENCY ERRORS FOUND.")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(validate_all())
