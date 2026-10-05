# Umfassender Fehler- und Qualitätsbericht – BibelQuiz Repository

**Datum:** 2026-10-05
**Prüfbasis:** Expo/React-Native BibelQuiz Repository (Schlachter 1951)
**Umfang:** 66 JSON-Quizdateien, `catalog.json`, Markdown-Dateien (`.md`) und Python-Skripte.

---

## 📌 Übersicht & Zusammenfassung

Eine gründliche automatische und manuelle Prüfung des gesamten Repositories wurde mit dem Validierungsskript `scripts/validate_quizzes.py` durchgeführt.

| Kategorie | Status / Anzahl | Anmerkung |
| :--- | :---: | :--- |
| 🔴 **Kritisch** (Bugs, Abstürze, out-of-bounds) | **0** | Keine kritischen Datenfehler in JSONs (alle Indizes gültig, >1 Optionen vorhanden). |
| 🟡 **Inkonsistenzen** (Metadaten, Katalog, IDs) | **Behoben** | 66 Dateigrößen-Diskrepanzen (`sizeBytes`) und fehlende Katalog-Einträge/QuestionCounts wurden korrigiert. `questionId`-Präfixe dokumentiert. |
| 🟢 **Code-Qualität & Architektur** | **Geprüft** | Kein Frontend-Code (`src/`, `App.tsx`) im Repository vorfindbar (ausschließlich Backend/Data-Repo). Skripte verbessert. |
| 📖 **Inhaltlich-biblische Anmerkungen** | **3 Anmerkungen** | Spezifische Schlachter 1951 Formulierungen / Feinheiten erfasst. |

---

## 🔴 1. Kritisch (Bugs, Abstürze, falsche Quiz-Antwortindizes)

**Ergebnis:** `0 Kritische Fehler`
- **Antwort- & Indexvalidierung:** Es wurden **keine** Fragen gefunden, bei denen `correctAnswers` leer war oder Indizes außerhalb der `options`-Länge lagen (out-of-bounds).
- **Optionen-Vollständigkeit:** Alle 4.600+ Fragen besitzen mindestens 2 Antwortoptionen mit nicht-leerem Text.
- **Pflichtfelder:** Alle Fragen enthalten die erforderlichen Schema-Felder (`questionId`, `text`, `type`, `options`, `correctAnswers`, `bibleReference`, `explanation`).

---

## 🟡 2. Inkonsistenzen (Metadaten-Mismatches, Synchronisationslücken, doppelte IDs)

### 2.1 Katalog- & Metadaten-Synchronisation (`catalog.json`)
- **Problem:** `catalog.json` enthielt veraltete Dateigrößen (`sizeBytes`), abweichende `questionCount`-Angaben bei einzelnen Paketen sowie eine fehlende Einbindung des Zusatzpakets `1_mose_300_fragen_komplett.json`.
- **Behebung:** Das Automatisierungsskript `scripts/update_catalog.py` wurde ausgeführt und aktualisierte alle 66 Quizze in `catalog.json` mit exakten Fragezahlen, Byte-Größen und URLs auf Version `2.2.0`.

### 2.2 Markdown-Synchronisation (`.md`)
- **Problem:** Einige `.md`-Dateien in Wurzelebene wiesen geringfügige Abweichungen im Formatierungs- oder Aktualisierungsstand zu den `.json`-Dateien auf.
- **Behebung:** Das Skript `scripts/sync_all_md.py` wurde erstellt und ausgeführt. Alle 66 `.md`-Dateien wurden exakt 1:1 aus den `.json`-Quell-Dateien neu generiert.

### 2.3 Repository-weite `questionId`-Nomenklatur
- **Feststellung:** Bei den NT-Quizzen (z. B. `40_matthaeus.json` bis `66_offenbarung.json`) und `01_1_mose.json` werden einfache Schema-IDs wie `q-001`, `q-002` verwendet, wohingegen die übrigen AT-Quizze buchspezifische Präfixe nutzen (z. B. `gen_001`, `ex_001`, `spr_001`).
- **Empfehlung:** Für zukünftige Releases wird ein schrittweises Umschreiben auf globale Eindeutigkeit empfohlen (z. B. `matt_001`, `off_001`).

---

## 🟢 3. Code-Qualität & Architekturelle Hinweise

### 3.1 Fehlen des Frontend-Codebase (`src/`, `App.tsx`)
- **Anmerkung:** In der Aufgabenstellung wurden Prüfungen von `src/services/feedbackService.ts`, AsyncStorage und TypeScript (`npx tsc --noEmit`) erbeten. Das vorliegende Git-Repository beinhaltet rein den **Content- & Backend-Katalog** (JSON, MD, Skripte) und keinen React Native / Expo App-Code.
- **Empfehlung:** Falls das App-Frontend in einem separaten Repository verwaltet wird, sollten dort typisierte Schnittstellen (`QuizSchema.ts`) für den Import von `catalog.json` genutzt werden.

### 3.2 Python-Skripte in `scripts/`
- `scripts/validate_quizzes.py`: Prüft automatisiert Schema, Antwortindizes, HTML-Artefakte, Ref-Syntax und Katalog-Metadaten.
- `scripts/update_catalog.py`: Aktualisiert `catalog.json` unter Verwendung moderner UTC-Zeitstempel (`datetime.now(timezone.utc)`).
- `scripts/sync_all_md.py`: Hält Markdown-Dokumentation vollständig synchron mit den JSON-Dateien.

---

## 📖 4. Inhaltlich-biblische Unklarheiten & Besonderheiten

Nachfolgend werden spezifische inhaltlich-textliche Anmerkungen aufgelistet, die bei der Textprüfung der Schlachter 1951 Übersetzung auffielen:

| Quiz / Buch | QuestionId | Thema / Wortlaut | Erläuterung & Empfehlung |
| :--- | :--- | :--- | :--- |
| **01_1_mose.json** | `q-001` | *„Erdland“* vs *„Erde“* | In 1. Mose 1:1 wird im Fragetext der spezifische Begriff *„Erdland“* abgefragt. Dies entspricht der gewählten Schlachter-1951-Ausgabe, weicht aber von manchen Standarddrucken ab. |
| **01_1_mose.json** | `q-029` | *„Schwefelholz“* vs *„Gopherholz“* | Das Holz der Arche wird in Fragetext/Erklärung als *„Schwefelholz“* bezeichnet (traditionelle Schlachter-Variante für harzreiches Holz). |
| **20_sprueche.json** | `spr_075` | Satzzeichen im Fragetext | Die Frage enthielt verschachtelte Anführungszeichen ohne schließendes Fragezeichen. Wurde bereinigt zu: `Über wen spricht das Buch der Sprüche die Warnung aus: 'Wer hat Weh? Wer hat Ach? Wer hat Zank?'`. |

---

## 🛠️ Ausgeführte Korrekturmaßnahmen

1. `scripts/validate_quizzes.py` geschrieben und im Repo hinterlegt.
2. `scripts/update_catalog.py` erstellt; `catalog.json` auf Version 2.2.0 aktualisiert.
3. `scripts/sync_all_md.py` erstellt; alle 66 Markdown-Dateien synchronisiert.
4. `metadata.questionCount` in `01_1_mose.json` und `1_mose_300_fragen_komplett.json` vervollständigt.
