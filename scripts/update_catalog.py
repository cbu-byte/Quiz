import json
import os
import glob
from datetime import datetime, timezone

def update_catalog():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    catalog_path = os.path.join(root_dir, "catalog.json")

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    json_files = glob.glob(os.path.join(root_dir, "*.json"))
    json_files = [f for f in json_files if not f.endswith("catalog.json")]

    quizzes_by_url = {}

    for filepath in sorted(json_files):
        filename = os.path.basename(filepath)
        rel_url = f"./{filename}"

        with open(filepath, "r", encoding="utf-8") as f:
            quiz_content = json.load(f)

        meta = quiz_content.get("metadata", {})
        questions = quiz_content.get("questions", [])
        real_count = len(questions)
        real_size = os.path.getsize(filepath)

        # Update metadata.questionCount in json if missing or mismatched
        if meta.get("questionCount") != real_count:
            meta["questionCount"] = real_count
            quiz_content["metadata"] = meta
            with open(filepath, "w", encoding="utf-8") as out_f:
                json.dump(quiz_content, out_f, ensure_ascii=False, indent=2)

        # Determine category
        category = "at"
        if filename.startswith("01_") or filename == "1_mose_300_fragen_komplett.json":
            category = "at" if filename == "1_mose_300_fragen_komplett.json" else "gesetz"
        elif filename.startswith(("02_", "03_", "04_", "05_")):
            category = "gesetz"
        elif filename.startswith(("06_", "07_", "08_", "09_", "10_", "11_", "12_", "13_", "14_", "15_", "16_", "17_")):
            category = "geschichte"
        elif filename.startswith(("18_", "20_", "21_", "22_")):
            category = "weisheit"
        elif filename.startswith(("23_", "24_", "25_", "26_", "27_", "28_", "29_", "30_", "31_", "32_", "33_", "34_", "35_", "36_", "37_", "38_", "39_")):
            category = "propheten"
        elif filename.startswith(("40_", "41_", "42_", "43_", "44_", "45_", "46_", "47_", "48_", "49_", "50_", "51_", "52_", "53_", "54_", "55_", "56_", "57_", "58_", "59_", "60_", "61_", "62_", "63_", "64_", "65_", "66_")):
            category = "nt"

        quiz_entry = {
            "quizId": meta.get("quizId", filename.replace(".json", "")),
            "category": category,
            "title": meta.get("title", filename),
            "subtitle": meta.get("subtitle", ""),
            "author": meta.get("author", "Schlachter 1951"),
            "version": meta.get("version", "2.0.0"),
            "questionCount": real_count,
            "difficulty": meta.get("difficulty", "medium"),
            "tags": meta.get("tags", ["Bibel-Quiz", "Schlachter 1951"]),
            "sizeBytes": real_size,
            "downloadUrl": rel_url
        }

        quizzes_by_url[rel_url] = quiz_entry

    new_quizzes_list = []

    for filepath in sorted(json_files):
        rel_url = f"./{os.path.basename(filepath)}"
        if rel_url in quizzes_by_url:
            new_quizzes_list.append(quizzes_by_url[rel_url])

    catalog_data["quizzes"] = new_quizzes_list
    catalog_data["catalogVersion"] = "2.2.0"
    catalog_data["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, ensure_ascii=False, indent=2)

    print(f"catalog.json updated successfully with {len(new_quizzes_list)} quizzes.")

if __name__ == "__main__":
    update_catalog()
