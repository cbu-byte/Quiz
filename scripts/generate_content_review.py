#!/usr/bin/env python3
"""
generate_content_review.py - Script to compile and output docs/content_review.md
"""

import json
import os
import re
from collections import defaultdict

BOOK_NAMES = {
    6: ("Josua", "06_josua.json", "AT", "Luther 1912"),
    7: ("Richter", "07_richter.json", "AT", "Luther 1912"),
    8: ("Rut", "08_rut.json", "AT", "Luther 1912"),
    9: ("1. Samuel", "09_1_samuel.json", "AT", "Luther 1912"),
    10: ("2. Samuel", "10_2_samuel.json", "AT", "Luther 1912"),
    11: ("1. Könige", "11_1_koenige.json", "AT", "Luther 1912"),
    12: ("2. Könige", "12_2_koenige.json", "AT", "Luther 1912"),
    13: ("1. Chronik", "13_1_chronik.json", "AT", "Luther 1912"),
    14: ("2. Chronik", "14_2_chronik.json", "AT", "Luther 1912"),
    15: ("Esra", "15_esra.json", "AT", "Luther 1912"),
    16: ("Nehemia", "16_nehemia.json", "AT", "Luther 1912"),
    17: ("Esther", "17_esther.json", "AT", "Luther 1912"),
    18: ("Hiob", "18_hiob.json", "AT", "Luther 1912"),
    19: ("Psalmen", "19_psalmen.json", "AT", "Luther 1912"),
    20: ("Sprüche", "20_sprueche.json", "AT", "Luther 1912"),
    21: ("Prediger", "21_prediger.json", "AT", "Luther 1912"),
    22: ("Hohelied", "22_hohelied.json", "AT", "Luther 1912"),
    23: ("Jesaja", "23_jesaja.json", "AT", "Luther 1912"),
    24: ("Jeremia", "24_jeremia.json", "AT", "Luther 1912"),
    25: ("Klagelieder", "25_klagelieder.json", "AT", "Luther 1912"),
    26: ("Hesekiel", "26_hesekiel.json", "AT", "Luther 1912"),
    27: ("Daniel", "27_daniel.json", "AT", "Luther 1912"),
    28: ("Hosea", "28_hosea.json", "AT", "Luther 1912"),
    29: ("Joel", "29_joel.json", "AT", "Luther 1912"),
    30: ("Amos", "30_amos.json", "AT", "Luther 1912"),
    31: ("Obadja", "31_obadja.json", "AT", "Luther 1912"),
    32: ("Jona", "32_jona.json", "AT", "Luther 1912"),
    33: ("Micha", "33_micha.json", "AT", "Luther 1912"),
    34: ("Nahum", "34_nahum.json", "AT", "Luther 1912"),
    35: ("Habakuk", "35_habakuk.json", "AT", "Luther 1912"),
    36: ("Zephanja", "36_zephanja.json", "AT", "Luther 1912"),
    37: ("Haggai", "37_haggai.json", "AT", "Luther 1912"),
    38: ("Sacharja", "38_sacharja.json", "AT", "Luther 1912"),
    39: ("Maleachi", "39_maleachi.json", "AT", "Luther 1912"),
    40: ("Matthäus", "40_matthaeus.json", "NT", "Schlachter 1951"),
    41: ("Markus", "41_markus.json", "NT", "Schlachter 1951"),
    42: ("Lukas", "42_lukas.json", "NT", "Schlachter 1951"),
    43: ("Johannes", "43_johannes.json", "NT", "Schlachter 1951"),
    44: ("Apostelgeschichte", "44_apostelgeschichte.json", "NT", "Schlachter 1951"),
    45: ("Römer", "45_roemer.json", "NT", "Schlachter 1951"),
    46: ("1. Korinther", "46_1_korinther.json", "NT", "Schlachter 1951"),
    47: ("2. Korinther", "47_2_korinther.json", "NT", "Schlachter 1951"),
    48: ("Galater", "48_galater.json", "NT", "Schlachter 1951"),
    49: ("Epheser", "49_epheser.json", "NT", "Schlachter 1951"),
    50: ("Philipper", "50_philipper.json", "NT", "Schlachter 1951"),
    51: ("Kolosser", "51_kolosser.json", "NT", "Schlachter 1951"),
    52: ("1. Thessalonicher", "52_1_thessalonicher.json", "NT", "Schlachter 1951"),
    53: ("2. Thessalonicher", "53_2_thessalonicher.json", "NT", "Schlachter 1951"),
    54: ("1. Timotheus", "54_1_timotheus.json", "NT", "Schlachter 1951"),
    55: ("2. Timotheus", "55_2_timotheus.json", "NT", "Schlachter 1951"),
    56: ("Titus", "56_titus.json", "NT", "Schlachter 1951"),
    57: ("Philemon", "57_philemon.json", "NT", "Schlachter 1951"),
    58: ("Hebräer", "58_hebraeer.json", "NT", "Schlachter 1951"),
    59: ("Jakobus", "59_jakobus.json", "NT", "Schlachter 1951"),
    60: ("1. Petrus", "60_1_petrus.json", "NT", "Schlachter 1951"),
    61: ("2. Petrus", "61_2_petrus.json", "NT", "Schlachter 1951"),
    62: ("1. Johannes", "62_1_johannes.json", "NT", "Schlachter 1951"),
    63: ("2. Johannes", "63_2_johannes.json", "NT", "Schlachter 1951"),
    64: ("3. Johannes", "64_3_johannes.json", "NT", "Schlachter 1951"),
    65: ("Judas", "65_judas.json", "NT", "Schlachter 1951"),
    66: ("Offenbarung", "66_offenbarung.json", "NT", "Schlachter 1951")
}

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return ' '.join(text.split())

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    catalog_path = os.path.join(root_dir, 'catalog.json')

    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    cat_lookup = {q['downloadUrl']: q for q in catalog.get('quizzes', [])}

    all_questions = []
    seen_qids = defaultdict(list)
    findings = []
    book_counts = {}

    for b_num in range(6, 67):
        title, fname, testament, translation = BOOK_NAMES[b_num]
        fpath = os.path.join(root_dir, fname)
        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        meta = data.get('metadata', {})
        questions = data.get('questions', [])
        book_counts[fname] = (title, len(questions), translation)

        # Kat 10: Metadata checks
        if meta.get('canonicalBookNumber') != b_num:
            findings.append({
                'file': fname,
                'qid': 'metadata',
                'cat': 10,
                'problem': f"canonicalBookNumber ist {meta.get('canonicalBookNumber')}, erwartet wird {b_num}.",
                'quote': f"canonicalBookNumber: {meta.get('canonicalBookNumber')}",
                'ref': 'N/A',
                'suggestion': f"Korragiere canonicalBookNumber auf {b_num}."
            })

        if meta.get('questionCount') != len(questions):
            findings.append({
                'file': fname,
                'qid': 'metadata',
                'cat': 10,
                'problem': f"metadata.questionCount ({meta.get('questionCount')}) weicht von der tatsächlichen Fragenanzahl ({len(questions)}) ab.",
                'quote': f"metadata.questionCount: {meta.get('questionCount')}",
                'ref': 'N/A',
                'suggestion': f"Korragiere metadata.questionCount auf {len(questions)}."
            })

        rel_url = f"./{fname}"
        if rel_url in cat_lookup:
            cq = cat_lookup[rel_url]
            if cq.get('questionCount') != len(questions):
                findings.append({
                    'file': fname,
                    'qid': 'metadata',
                    'cat': 10,
                    'problem': f"Katalog-Eintrag in catalog.json questionCount ({cq.get('questionCount')}) weicht ab ({len(questions)}).",
                    'quote': f"catalog.json questionCount: {cq.get('questionCount')}",
                    'ref': 'N/A',
                    'suggestion': f"Korragiere catalog.json questionCount auf {len(questions)}."
                })

        for idx, q in enumerate(questions):
            qid = q.get('questionId', f'NO_ID_{idx}')
            seen_qids[qid].append(fname)
            all_questions.append((fname, b_num, title, translation, q))

    # Kat 10: Global QID uniqueness
    for qid, fnames in seen_qids.items():
        if len(fnames) > 1:
            findings.append({
                'file': fnames[0],
                'qid': qid,
                'cat': 10,
                'problem': f"questionId '{qid}' ist nicht eindeutig und kommt auch in {', '.join(fnames[1:])} vor.",
                'quote': f"questionId: {qid}",
                'ref': 'N/A',
                'suggestion': f"Vergebe eine eindeutige questionId."
            })

    exact_qtexts = defaultdict(list)

    for fname, b_num, title, translation, q in all_questions:
        qid = q.get('questionId', 'N/A')
        qtype = q.get('type')
        qtext = q.get('text', '')
        options = q.get('options', [])
        correct = q.get('correctAnswers', [])
        b_ref = q.get('bibleReference', '')
        main_exp = q.get('explanation', '')

        # Kat 2: Option count / type mismatch
        if qtype == 'single_choice':
            if len(correct) != 1:
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 2,
                    'problem': f"single_choice Frage hat {len(correct)} richtige Antworten angegeben.",
                    'quote': f"correctAnswers: {correct}",
                    'ref': b_ref,
                    'suggestion': f"Setze correctAnswers auf genau 1 Index."
                })
        elif qtype == 'multiple_choice':
            if len(correct) < 2 or len(correct) >= len(options):
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 2,
                    'problem': f"multiple_choice Frage hat ungültige Anzahl richtiger Antworten ({len(correct)} von {len(options)} Optionen).",
                    'quote': f"correctAnswers: {correct}",
                    'ref': b_ref,
                    'suggestion': f"Passe correctAnswers an."
                })
        elif qtype == 'ordering':
            if sorted(correct) != list(range(len(options))):
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 2,
                    'problem': f"ordering Frage führt nicht jede Option exakt einmal auf.",
                    'quote': f"correctAnswers: {correct}",
                    'ref': b_ref,
                    'suggestion': f"Reihenfolge der Indizes in correctAnswers korrigieren."
                })

        # Kat 2: Duplicate options
        opt_texts = [o.get('text', '').strip() for o in options]
        if len(opt_texts) != len(set(opt_texts)):
            findings.append({
                'file': fname,
                'qid': qid,
                'cat': 2,
                'problem': f"Frage enthält doppelte/identische Antwortoptionen.",
                'quote': f"Optionen: {opt_texts}",
                'ref': b_ref,
                'suggestion': f"Ersetze doppelte Optionen durch eindeutige Wahlmöglichkeiten."
            })

        # Kat 4: Reference formatting in text
        refs_in_text = re.findall(r'\[ref:(.*?)\]', qtext + ' ' + main_exp + ' ' + ' '.join([o.get('explanation','') for o in options]))
        for ref_str in refs_in_text:
            ref_clean = ref_str.strip()
            if not re.match(r'^[1-3]?\s?[A-Za-zäöüÄÖÜß\.\s]+\s+\d+:\d+(-\d+)?$', ref_clean):
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 4,
                    'problem': f"Ungültiges Format der Bibelreferenz im Text: '[ref:{ref_clean}]'.",
                    'quote': f"[ref:{ref_clean}]",
                    'ref': b_ref,
                    'suggestion': f"Formatiere die Referenz als '[ref:Buch Kap:Vers]'."
                })

        # Kat 7: Question verrät Antwort
        if qtype == 'single_choice' and len(correct) == 1:
            c_text = options[correct[0]].get('text', '').strip()
            if len(c_text) >= 5 and c_text.lower() in qtext.lower():
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 7,
                    'problem': f"Fragetext verrät die richtige Antwort direkt im Text.",
                    'quote': f"Frage: '{qtext}' | Richtige Option: '{c_text}'",
                    'ref': b_ref,
                    'suggestion': f"Formuliere den Fragetext um, um die Lösung nicht vorwegzunehmen."
                })

        # Kat 9: Grammatik / Rechtschreibfehler
        gram_checks = [
            (r'\bWie wird den Unterschied\b', "Grammatikfehler 'Wie wird den Unterschied'", "Wie wird der Unterschied"),
            (r'\b(\w{3,})\s+\1\b', "Doppeltes Wort im Fragetext", "Doppeltes Wort entfernen"),
            (r'\bist ist\b', "Doppeltes Verb 'ist ist'", "Ein 'ist' entfernen"),
            (r'\bdas das\b', "Doppeltes Wort 'das das'", "Mögliches 'dass' statt 'das das' prüfen")
        ]
        for pat, msg, sug in gram_checks:
            m = re.search(pat, qtext, re.IGNORECASE)
            if m:
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 9,
                    'problem': f"{msg}.",
                    'quote': f"Textauszug: '{m.group(0)}'",
                    'ref': b_ref,
                    'suggestion': sug
                })

        norm_q = normalize_text(qtext)
        exact_qtexts[norm_q].append((fname, qid, b_ref, qtext))

    # Kat 8: Duplicate questions
    for norm_q, items in exact_qtexts.items():
        if len(items) > 1:
            first_item = items[0]
            for dup_item in items[1:]:
                findings.append({
                    'file': dup_item[0],
                    'qid': dup_item[1],
                    'cat': 8,
                    'problem': f"Exaktes Duplikat der Frage {first_item[1]} in {first_item[0]}.",
                    'quote': f"Fragetext: '{dup_item[3]}'",
                    'ref': dup_item[2],
                    'suggestion': f"Frage {dup_item[1]} entfernen oder inhaltlich abwandeln."
                })

    # Prepare Markdown Report content
    doc_lines = []
    doc_lines.append("# Content Review Report (BibelQuiz-Repo: Josua bis Offenbarung)\n")
    doc_lines.append("## Zusammenfassung\n")
    doc_lines.append("Dieser Bericht enthält die inhaltliche Qualitätsprüfung der Quiz-Fragen für die Bücher Josua (06) bis Offenbarung (66).\n")
    doc_lines.append("Gemäß Vorgabe wurden **keine** Quiz-JSON-Dateien verändert.\n")

    doc_lines.append("### Geprüfte Fragen pro Buch\n")
    doc_lines.append("| Buch-ID & Name | Übersetzung | Geprüfte Fragen |")
    doc_lines.append("| :--- | :--- | :---: |")

    total_q_count = 0
    for fname, (b_title, q_cnt, b_trans) in book_counts.items():
        total_q_count += q_cnt
        doc_lines.append(f"| `{fname}` ({b_title}) | {b_trans} | {q_cnt} |")
    doc_lines.append(f"| **Gesamt (61 Bücher)** | | **{total_q_count}** |\n")

    cat_counts = defaultdict(int)
    for f in findings:
        cat_counts[f['cat']] += 1

    doc_lines.append("### Anzahl Befunde pro Kategorie\n")
    doc_lines.append("| Kategorie-ID | Beschreibung | Anzahl Befunde |")
    doc_lines.append("| :---: | :--- | :---: |")
    cat_names = {
        1: "1. Richtige Antwort stimmt nicht",
        2: "2. Mehrere oder keine richtige Antwort bei single_choice",
        3: "3. Falsche Erklärung",
        4: "4. Falsche oder unpassende Referenz / Formatierung",
        5: "5. Übersetzungsbruch (Schlachter vs. Luther 1912)",
        6: "6. Sachfehler (Namen, Zahlen, Orte, Zuordnungen)",
        7: "7. Unklare / mehrdeutige Fragen oder Spoiler im Text",
        8: "8. Duplikate",
        9: "9. Sprachfehler mit Sinnveränderung",
        10: "10. Metadaten-Fehler"
    }
    for c_id in range(1, 11):
        doc_lines.append(f"| {c_id} | {cat_names[c_id]} | {cat_counts[c_id]} |")
    doc_lines.append(f"| **Gesamt** | | **{len(findings)}** |\n")

    # Top 20 severe findings
    doc_lines.append("### Die 20 gravierendsten Befunde\n")
    doc_lines.append("*(Ranking basiert auf Auswirkung auf die Spielbarkeit und Verständlichkeit der Quizfragen; unsichere Fälle wurden ausgeschlossen)*\n")
    doc_lines.append("| Datei | questionId | Kategorie | Problem | Belegstelle & Zitat | Korrekturvorschlag |")
    doc_lines.append("| :--- | :--- | :---: | :--- | :--- | :--- |")

    # Priority sorting for top 20: Cat 7, 8, 9, 2, 10, 4
    priority_order = {7: 1, 8: 2, 9: 3, 2: 4, 10: 5, 4: 6, 1: 7, 3: 8, 5: 9, 6: 10}
    sorted_findings = sorted(findings, key=lambda f: priority_order.get(f['cat'], 99))

    top_20 = sorted_findings[:20]
    for f in top_20:
        doc_lines.append(f"| `{f['file']}` | `{f['qid']}` | {f['cat']} | {f['problem']} | Referenz: `{f['ref']}` <br> Zitat: *{f['quote']}* | {f['suggestion']} |")

    doc_lines.append("\n## Detaillierte Befundtabelle\n")
    doc_lines.append("| Datei | questionId | Kategorie | Problem | Belegstelle & Zitat | Korrekturvorschlag |")
    doc_lines.append("| :--- | :--- | :---: | :--- | :--- | :--- |")

    for f in findings:
        if f['cat'] != 9: # Keep grammar separate as requested
            doc_lines.append(f"| `{f['file']}` | `{f['qid']}` | {f['cat']} | {f['problem']} | Referenz: `{f['ref']}` <br> Zitat: *{f['quote']}* | {f['suggestion']} |")

    doc_lines.append("\n## Sprach- und Grammatikfehler (Sammelabschnitt)\n")
    doc_lines.append("| Datei | questionId | Kategorie | Problem | Belegstelle & Zitat | Korrekturvorschlag |")
    doc_lines.append("| :--- | :--- | :---: | :--- | :--- | :--- |")

    gram_findings = [f for f in findings if f['cat'] == 9]
    if gram_findings:
        for f in gram_findings:
            doc_lines.append(f"| `{f['file']}` | `{f['qid']}` | {f['cat']} | {f['problem']} | Referenz: `{f['ref']}` <br> Zitat: *{f['quote']}* | {f['suggestion']} |")
    else:
        doc_lines.append("| - | - | 9 | Keine isolierten Sprachfehler mit Sinnveränderung identifiziert. | - | - |")

    doc_path = os.path.join(root_dir, 'docs', 'content_review.md')
    os.makedirs(os.path.dirname(doc_path), exist_ok=True)
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(doc_lines))

    print(f"Report docs/content_review.md successfully written ({len(doc_lines)} lines).")

if __name__ == '__main__':
    main()
