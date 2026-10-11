#!/usr/bin/env python3
"""
update_catalog.py - Update catalog.json based on canonical quiz JSON files.
"""

import json
import glob
import os
import sys

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    catalog_path = os.path.join(root_dir, 'catalog.json')

    if not os.path.exists(catalog_path):
        print("ERROR: catalog.json not found!")
        sys.exit(1)

    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)

    quizzes_json_dir = os.path.join(root_dir, 'quizzes', 'json')
    if os.path.exists(quizzes_json_dir) and glob.glob(os.path.join(quizzes_json_dir, '*.json')):
        json_files = sorted(glob.glob(os.path.join(quizzes_json_dir, '*.json')))
        is_quizzes_subdir = True
    else:
        json_files = sorted([
            f for f in glob.glob(os.path.join(root_dir, '*.json'))
            if not f.endswith('catalog.json') and not f.endswith('1_mose_300_fragen_komplett.json')
        ])
        is_quizzes_subdir = False

    updated_quizzes = []

    for file_path in json_files:
        filename = os.path.basename(file_path)
        if is_quizzes_subdir:
            rel_url = f"./quizzes/json/{filename}"
        else:
            rel_url = f"./{filename}"

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        meta = data.get('metadata', {})
        questions = data.get('questions', [])

        actual_count = len(questions)
        actual_size = os.path.getsize(file_path)

        quiz_entry = {
            "quizId": meta.get("quizId"),
            "category": meta.get("category"),
            "title": meta.get("title"),
            "subtitle": meta.get("subtitle"),
            "author": meta.get("author", "Schlachter 1951"),
            "version": meta.get("version", "2.1.0"),
            "questionCount": actual_count,
            "difficulty": meta.get("difficulty", "medium"),
            "tags": meta.get("tags", []),
            "sizeBytes": actual_size,
            "downloadUrl": rel_url
        }
        updated_quizzes.append(quiz_entry)

    catalog_data['quizzes'] = updated_quizzes

    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(catalog_data, f, ensure_ascii=False, indent=2)
        f.write('\n')

    # Also sync catalog.json copy to quizzes/catalog.json if quizzes dir exists
    quizzes_dir = os.path.join(root_dir, 'quizzes')
    if os.path.exists(quizzes_dir):
        quizzes_catalog_path = os.path.join(quizzes_dir, 'catalog.json')
        with open(quizzes_catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog_data, f, ensure_ascii=False, indent=2)
            f.write('\n')

    print(f"Successfully updated catalog.json with {len(updated_quizzes)} quizzes.")

if __name__ == '__main__':
    main()
