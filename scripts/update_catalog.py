#!/usr/bin/env python3
"""
Script to update catalog.json with all quiz files, accurate question counts, sizeBytes, and metadata.
"""

import os
import glob
import json
from datetime import datetime, timezone

def update_catalog():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    catalog_path = os.path.join(root_dir, "catalog.json")

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    json_files = sorted(glob.glob(os.path.join(root_dir, "*.json")))
    quiz_files = [f for f in json_files if os.path.basename(f) != "catalog.json"]

    existing_quizzes = catalog.get("quizzes", [])
    quiz_by_url = {q.get("downloadUrl"): q for q in existing_quizzes}

    updated_quizzes = []

    for filepath in quiz_files:
        filename = os.path.basename(filepath)
        download_url = f"./{filename}"
        file_size = os.path.getsize(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("metadata", {})
        questions = data.get("questions", [])
        question_count = len(questions)

        quiz_id = meta.get("quizId", os.path.splitext(filename)[0])

        entry = {
            "quizId": quiz_id,
            "category": meta.get("category", "at"),
            "title": meta.get("title", filename),
            "subtitle": meta.get("subtitle", ""),
            "author": meta.get("author", "Schlachter 1951"),
            "version": meta.get("version", "2.0.0"),
            "questionCount": question_count,
            "difficulty": meta.get("difficulty", "medium"),
            "tags": meta.get("tags", [meta.get("title", "Bibel-Quiz")]),
            "sizeBytes": file_size,
            "downloadUrl": download_url,
            "canonicalBookNumber": meta.get("canonicalBookNumber"),
            "testament": meta.get("testament")
        }

        updated_quizzes.append(entry)

    catalog["catalogVersion"] = "2.2.0"
    catalog["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    catalog["quizzes"] = updated_quizzes

    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Updated catalog.json with {len(updated_quizzes)} quizzes.")

if __name__ == "__main__":
    update_catalog()
