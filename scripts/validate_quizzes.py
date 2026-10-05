import json
import os
import re
import glob

def validate():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_files = glob.glob(os.path.join(root_dir, "*.json"))
    json_files = [f for f in json_files if not f.endswith("catalog.json")]

    catalog_path = os.path.join(root_dir, "catalog.json")

    report = {
        "critical": [],
        "inconsistencies": [],
        "quality": [],
        "biblical_content_notes": []
    }

    all_question_ids = {} # questionId -> list of (filename, q_index)
    catalog_data = None

    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog_data = json.load(f)
        except Exception as e:
            report["critical"].append(f"catalog.json ist ungültiges JSON: {e}")

    catalog_quizzes = {}
    if catalog_data and "quizzes" in catalog_data:
        for q in catalog_data["quizzes"]:
            catalog_quizzes[q.get("downloadUrl", "")] = q

    REQUIRED_Q_FIELDS = ["questionId", "text", "type", "options", "correctAnswers", "bibleReference", "explanation"]

    for filepath in sorted(json_files):
        filename = os.path.basename(filepath)
        rel_path = f"./{filename}"

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            report["critical"].append(f"{filename}: Ungültiges JSON-Format: {e}")
            continue

        metadata = data.get("metadata", {})
        questions = data.get("questions", [])

        # 1. Metadaten Check
        claimed_count = metadata.get("questionCount")
        actual_count = len(questions)
        if claimed_count != actual_count:
            report["inconsistencies"].append(
                f"{filename}: metadata.questionCount ({claimed_count}) stimmt nicht mit tatsächlicher Fragenanzahl ({actual_count}) überein."
            )

        # 2. Catalog Check
        if catalog_data:
            if rel_path not in catalog_quizzes:
                report["inconsistencies"].append(f"Katalog: Datei {filename} ({rel_path}) fehlt in catalog.json.")
            else:
                cat_entry = catalog_quizzes[rel_path]
                if cat_entry.get("questionCount") != actual_count:
                    report["inconsistencies"].append(
                        f"Katalog Mismatch [{filename}]: catalog.json questionCount ({cat_entry.get('questionCount')}) != real count ({actual_count})."
                    )
                if cat_entry.get("quizId") != metadata.get("quizId"):
                    report["inconsistencies"].append(
                        f"Katalog Mismatch [{filename}]: catalog.json quizId ({cat_entry.get('quizId')}) != metadata.quizId ({metadata.get('quizId')})."
                    )
                real_size = os.path.getsize(filepath)
                if cat_entry.get("sizeBytes") != real_size:
                    report["inconsistencies"].append(
                        f"Katalog Mismatch [{filename}]: catalog.json sizeBytes ({cat_entry.get('sizeBytes')}) != real file size ({real_size})."
                    )

        # 3. Fragen Check
        for idx, q in enumerate(questions):
            q_id = q.get("questionId", f"index-{idx}")

            # Repo-wide questionId check
            if q_id in all_question_ids:
                prev_file, prev_idx = all_question_ids[q_id]
                report["inconsistencies"].append(
                    f"Doppelte questionId '{q_id}' in {filename} (Frage {idx+1}) und {prev_file} (Frage {prev_idx+1})."
                )
            else:
                all_question_ids[q_id] = (filename, idx)

            # Pflichtfelder Check
            for field in REQUIRED_Q_FIELDS:
                if field not in q or q[field] is None:
                    report["critical"].append(
                        f"{filename} [{q_id}]: Pflichtfeld '{field}' fehlt."
                    )

            # Option & Answer Validation
            options = q.get("options", [])
            correct_answers = q.get("correctAnswers", [])

            if not isinstance(options, list) or len(options) < 2:
                report["critical"].append(
                    f"{filename} [{q_id}]: Weniger als 2 Antwortmöglichkeiten ({len(options) if isinstance(options, list) else 'ungültig'})."
                )

            if not isinstance(correct_answers, list) or len(correct_answers) == 0:
                report["critical"].append(
                    f"{filename} [{q_id}]: correctAnswers ist leer oder kein Array."
                )
            else:
                for ca in correct_answers:
                    if not isinstance(ca, int) or ca < 0 or ca >= len(options):
                        report["critical"].append(
                            f"{filename} [{q_id}]: correctAnswers Index {ca} ist out-of-bounds für {len(options)} Optionen."
                        )

            # Incomplete options text
            for opt_idx, opt in enumerate(options if isinstance(options, list) else []):
                if isinstance(opt, dict):
                    opt_text = opt.get("text", "")
                    if not opt_text or not opt_text.strip():
                        report["critical"].append(f"{filename} [{q_id}]: Option {opt_idx+1} hat leeren Text.")
                else:
                    report["critical"].append(f"{filename} [{q_id}]: Option {opt_idx+1} ist kein Objekt.")

            # Text & Ref Checks
            text = q.get("text", "")
            explanation = q.get("explanation", "")
            bible_ref = q.get("bibleReference", "")

            # HTML Artifacts
            for check_str, field_name in [(text, "text"), (explanation, "explanation")]:
                if re.search(r"<[^>]+>|&nbsp;|&amp;|&quot;|&#39;", check_str):
                    report["quality"].append(
                        f"{filename} [{q_id}]: HTML-Artefakte oder Entitäten in '{field_name}' gefunden: '{check_str[:60]}...'"
                    )

            # Check ref tags syntax e.g. [ref:...]
            # Find all occurrences of [ref: or similar
            ref_matches = re.findall(r"\[ref:[^\]]*", explanation)
            for rm in ref_matches:
                if not rm.endswith("]"): # wait, re.findall with [ref:[^\]]* won't include closing bracket if regex didn't demand it
                    pass
            # Check for broken ref tags e.g. [ref: without ]
            if "[ref:" in explanation:
                # verify all [ref: have a matching ]
                open_count = explanation.count("[ref:")
                # count properly closed [ref:...]
                closed_count = len(re.findall(r"\[ref:[^\]]+\]", explanation))
                if open_count != closed_count:
                    report["inconsistencies"].append(
                        f"{filename} [{q_id}]: Fehlerhafte [ref:...]-Syntax in Erklärung: '{explanation}'"
                    )

            # Abgebrochene Sätze / Kurze Texte
            if text and not text.strip().endswith(("?", ".", "!", "“", "»", "”")):
                report["quality"].append(
                    f"{filename} [{q_id}]: Fragetext endet nicht mit Satzzeichen: '{text}'"
                )

        # 4. Markdown Sync Check
        md_filename = filename.replace(".json", ".md")
        md_filepath = os.path.join(root_dir, md_filename)
        if not os.path.exists(md_filepath):
            report["inconsistencies"].append(f"Markdown: Fehlende Markdown-Datei '{md_filename}' zu '{filename}'.")
        else:
            # Simple line/count check or existence check
            with open(md_filepath, "r", encoding="utf-8") as mdf:
                md_content = mdf.read()
                # Count questions in markdown (e.g., lines starting with ### Frage or ## Frage or ### q-)
                md_q_count = len(re.findall(r"^###?\s+(Frage|q-|\d+\.)", md_content, re.MULTILINE))
                # Note if counts differ wildly
                if md_q_count > 0 and md_q_count != actual_count:
                    report["inconsistencies"].append(
                        f"Markdown Sync [{md_filename}]: MD Fragenanzahl (~{md_q_count}) != JSON Fragenanzahl ({actual_count})."
                    )

    print("=== VALIDATION RESULTS ===")
    print(f"Kritisch: {len(report['critical'])}")
    for item in report["critical"]:
        print(f"  🔴 {item}")

    print(f"\nInkonsistenzen: {len(report['inconsistencies'])}")
    for item in report["inconsistencies"]:
        print(f"  🟡 {item}")

    print(f"\nCode-Qualität / Warnungen: {len(report['quality'])}")
    for item in report["quality"][:30]: # print first 30
        print(f"  🟢 {item}")
    if len(report["quality"]) > 30:
        print(f"  ... und {len(report['quality'])-30} weitere Quality-Warnungen.")

    return report

if __name__ == "__main__":
    validate()
