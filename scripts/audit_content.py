#!/usr/bin/env python3
"""
audit_content.py - Comprehensive content auditor for quiz files 06_josua.json to 66_offenbarung.json.
Generates structured findings for docs/content_review.md.
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
        book_counts[fname] = len(questions)

        # Kat 10: Metadata checks
        if meta.get('canonicalBookNumber') != b_num:
            findings.append({
                'file': fname,
                'qid': 'metadata',
                'cat': 10,
                'problem': f"canonicalBookNumber ist {meta.get('canonicalBookNumber')}, statt {b_num}.",
                'ref': 'N/A',
                'quote': 'metadata.canonicalBookNumber',
                'suggestion': f"Korragiere canonicalBookNumber auf {b_num}."
            })

        if meta.get('questionCount') != len(questions):
            findings.append({
                'file': fname,
                'qid': 'metadata',
                'cat': 10,
                'problem': f"metadata.questionCount ({meta.get('questionCount')}) weicht von der tatsächlichen Fragenanzahl ({len(questions)}) ab.",
                'ref': 'N/A',
                'quote': 'metadata.questionCount',
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
                    'problem': f"Katalog-Eintrag questionCount ({cq.get('questionCount')}) weicht von der tatsächlichen Fragenanzahl ({len(questions)}) ab.",
                    'ref': 'N/A',
                    'quote': 'catalog.json entry',
                    'suggestion': f"Korragiere catalog.json questionCount auf {len(questions)}."
                })

        for idx, q in enumerate(questions):
            qid = q.get('questionId', f'NO_ID_{idx}')
            seen_qids[qid].append(fname)
            all_questions.append((fname, b_num, title, translation, q))

    # Kat 10: Check duplicate questionIds globally
    for qid, fnames in seen_qids.items():
        if len(fnames) > 1:
            findings.append({
                'file': fnames[0],
                'qid': qid,
                'cat': 10,
                'problem': f"questionId '{qid}' ist nicht eindeutig und kommt auch in {', '.join(fnames[1:])} vor.",
                'ref': 'N/A',
                'quote': f"questionId: {qid}",
                'suggestion': f"Vergebe eine eindeutige questionId für jede betroffene Frage."
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

        # Kat 2: Option types and indices
        if qtype == 'single_choice':
            if len(correct) != 1:
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 2,
                    'problem': f"single_choice Frage hat {len(correct)} richtige Antworten angegeben.",
                    'ref': b_ref,
                    'quote': f"correctAnswers: {correct}",
                    'suggestion': f"Setze correctAnswers auf genau eine richtige Antwort."
                })
        elif qtype == 'multiple_choice':
            if len(correct) < 2 or len(correct) >= len(options):
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 2,
                    'problem': f"multiple_choice Frage hat ungültige Anzahl richtiger Antworten ({len(correct)} von {len(options)} Option).",
                    'ref': b_ref,
                    'quote': f"correctAnswers: {correct}",
                    'suggestion': f"Passe correctAnswers für multiple_choice an."
                })
        elif qtype == 'ordering':
            if sorted(correct) != list(range(len(options))):
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 2,
                    'problem': f"ordering Frage führt nicht jede Option exakt einmal in correctAnswers auf.",
                    'ref': b_ref,
                    'quote': f"correctAnswers: {correct}",
                    'suggestion': f"Reihenfolge der Indizes in correctAnswers korrigieren."
                })

        # Kat 2: Duplicate option texts
        opt_texts = [o.get('text', '').strip() for o in options]
        if len(opt_texts) != len(set(opt_texts)):
            findings.append({
                'file': fname,
                'qid': qid,
                'cat': 2,
                'problem': f"Frage enthält doppelte/identische Antwortoptionen.",
                'ref': b_ref,
                'quote': f"Optionen: {opt_texts}",
                'suggestion': f"Ersetze doppelte Optionen durch eindeutige Wahlmöglichkeiten."
            })

        # Kat 4: Bible reference formatting in refs
        refs_in_text = re.findall(r'\[ref:(.*?)\]', qtext + ' ' + main_exp + ' ' + ' '.join([o.get('explanation','') for o in options]))
        for ref_str in refs_in_text:
            ref_clean = ref_str.strip()
            if not re.match(r'^[1-3]?\s?[A-Za-zäöüÄÖÜß\.\s]+\s+\d+:\d+(-\d+)?$', ref_clean):
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 4,
                    'problem': f"Ungültiges Format der Bibelreferenz im Text: '[ref:{ref_clean}]'.",
                    'ref': b_ref,
                    'quote': f"[ref:{ref_clean}]",
                    'suggestion': f"Formatiere die Referenz als '[ref:Buch Kap:Vers]'."
                })

        # Kat 7: Question text gives away answer
        if qtype == 'single_choice' and len(correct) == 1:
            c_text = options[correct[0]].get('text', '').strip()
            if len(c_text) >= 5 and c_text.lower() in qtext.lower():
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 7,
                    'problem': f"Fragetext verrät die richtige Antwort direkt im Text.",
                    'ref': b_ref,
                    'quote': f"Frage: '{qtext}' | Option: '{c_text}'",
                    'suggestion': f"Formuliere den Fragetext um, um die Antwort nicht vorwegzunehmen."
                })

        # Kat 9: Grammatical / spelling issues affecting sense or phrasing
        gram_checks = [
            (r'\bWie wird den Unterschied\b', "Grammatikfehler 'Wie wird den Unterschied'", "Wie wird der Unterschied"),
            (r'\b(\w{3,})\s+\1\b', "Doppeltes Wort im Text", "Doppeltes Wort entfernen"),
            (r'\bist ist\b', "Doppeltes Verb 'ist ist'", "Ein 'ist' entfernen"),
            (r'\bdas das\b', "Doppeltes Wort 'das das'", "Wort wiederholung prüfen"),
        ]
        for pat, msg, sug in gram_checks:
            m = re.search(pat, qtext, re.IGNORECASE)
            if m:
                findings.append({
                    'file': fname,
                    'qid': qid,
                    'cat': 9,
                    'problem': f"{msg} im Fragetext.",
                    'ref': b_ref,
                    'quote': m.group(0),
                    'suggestion': sug
                })

        # Kat 8: Collect normalized text for duplicates
        norm_q = normalize_text(qtext)
        exact_qtexts[norm_q].append((fname, qid, b_ref, qtext))

    # Kat 8: Exact duplicate questions across files
    for norm_q, items in exact_qtexts.items():
        if len(items) > 1:
            first_item = items[0]
            for dup_item in items[1:]:
                findings.append({
                    'file': dup_item[0],
                    'qid': dup_item[1],
                    'cat': 8,
                    'problem': f"Exaktes Duplikat der Frage {first_item[1]} in {first_item[0]}.",
                    'ref': dup_item[2],
                    'quote': f"Frage: '{dup_item[3]}'",
                    'suggestion': f"Frage {dup_item[1]} entfernen oder inhaltlich abwandeln."
                })

    print(f"Audit completed: {len(findings)} findings generated across {len(book_counts)} books ({sum(book_counts.values())} questions).")

    # Output stats
    cat_counts = defaultdict(int)
    for f in findings:
        cat_counts[f['cat']] += 1

    print("\nFindings per Category:")
    for c in sorted(cat_counts.keys()):
        print(f" Category {c}: {cat_counts[c]}")

    return book_counts, findings, cat_counts

if __name__ == '__main__':
    main()
