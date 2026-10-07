#!/usr/bin/env python3
"""
update_catalog.py
Updates catalog.json with exact question counts, file sizes (sizeBytes), and metadata
from all canonical quiz JSON files in the repository. Supports both top-level
quizzes array and nested category quizzes arrays.
"""

import datetime
import json
import os
import sys

CATALOG_PATH = "catalog.json"

def process_quiz_entry(quiz_entry):
    download_url = quiz_entry.get("downloadUrl", "")
    file_path = download_url.lstrip("./")

    if not os.path.exists(file_path):
        print(f"Warning: Referenced file {file_path} does not exist.")
        return False

    size_bytes = os.path.getsize(file_path)

    with open(file_path, "r", encoding="utf-8") as qf:
        qdata = json.load(qf)

    meta = qdata.get("metadata", {})
    questions = qdata.get("questions", [])
    actual_qcount = len(questions)

    # Update quiz entry fields
    quiz_entry["questionCount"] = actual_qcount
    quiz_entry["sizeBytes"] = size_bytes

    if "quizId" in meta:
        quiz_entry["quizId"] = meta["quizId"]
    if "version" in meta:
        quiz_entry["version"] = meta["version"]
    if "title" in meta:
        quiz_entry["title"] = meta["title"]
    if "subtitle" in meta:
        quiz_entry["subtitle"] = meta["subtitle"]
    if "author" in meta:
        quiz_entry["author"] = meta["author"]
    if "difficulty" in meta:
        quiz_entry["difficulty"] = meta["difficulty"]
    if "tags" in meta:
        quiz_entry["tags"] = meta["tags"]

    # Also sync metadata.questionCount in the JSON file if it differs
    if meta.get("questionCount") != actual_qcount:
        meta["questionCount"] = actual_qcount
        qdata["metadata"] = meta
        with open(file_path, "w", encoding="utf-8") as qf:
            json.dump(qdata, qf, ensure_ascii=False, indent=2)
            qf.write("\n")

    return True

def update_catalog():
    if not os.path.exists(CATALOG_PATH):
        print(f"Error: {CATALOG_PATH} not found.")
        sys.exit(1)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    updated_count = 0

    # Top-level quizzes
    if "quizzes" in catalog and isinstance(catalog["quizzes"], list):
        for quiz_entry in catalog["quizzes"]:
            if process_quiz_entry(quiz_entry):
                updated_count += 1

    # Nested category quizzes
    if "categories" in catalog and isinstance(catalog["categories"], list):
        for category in catalog["categories"]:
            if "quizzes" in category and isinstance(category["quizzes"], list):
                for quiz_entry in category["quizzes"]:
                    if process_quiz_entry(quiz_entry):
                        updated_count += 1

    # Update top-level catalog timestamp
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    catalog["lastUpdated"] = now_iso

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Successfully updated catalog.json with {updated_count} quiz entries. Timestamp: {now_iso}")

if __name__ == "__main__":
    update_catalog()
