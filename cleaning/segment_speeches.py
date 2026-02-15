import re
import json
import os
import unicodedata
from datetime import datetime
import pandas as pd


# =========================================================
# PATH CONFIG
# =========================================================

CLEANED_TEXT_DIR = "data/cleaned_text"
STRUCTURED_DIR = "data/structured"

os.makedirs(STRUCTURED_DIR, exist_ok=True)


# =========================================================
# 1. METADATA EXTRACTION
# =========================================================

def extract_metadata_from_filename(filepath):
    filename = os.path.basename(filepath)

    match = re.search(r'lsd_(\d+)_(\d+)_(\d{2}-\d{2}-\d{4})', filename)

    if match:
        lok_sabha_number = int(match.group(1))
        session_number = int(match.group(2))
        date_str = match.group(3)
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    else:
        return None

    return {
        "debate_id": f"{lok_sabha_number}_{session_number}_{date_str}",
        "date": date_obj.strftime("%Y-%m-%d"),
        "year": date_obj.year,
        "month": date_obj.month,
        "lok_sabha_number": lok_sabha_number,
        "session_number": session_number,
        "source_file": filename
    }


# =========================================================
# 2. GLOBAL CLEANING
# =========================================================

def clean_global_text(text):

    text = unicodedata.normalize("NFKC", text)

    text = re.sub(r'[�]', '', text)
    text = re.sub(r'\u200b', '', text)
    text = re.sub(r'\xa0', ' ', text)

    text = re.sub(r'©\s*\d{4}.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'INTERNET\s+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'LIVE TELECAST.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'Published under Rules.*$', '', text, flags=re.MULTILINE)

    return text


# =========================================================
# 3. SPEAKER DETECTION
# =========================================================

SPEAKER_PATTERN = re.compile(
    r'^(?P<speaker>'
    r'(HON\. SPEAKER|HON\. CHAIRPERSON|SECRETARY[- ]GENERAL|'
    r'(?:SHRI|SHRIMATI|DR\.)\s+[A-Z][A-Z\s\.\-\(\)]*|'
    r'THE[\sA-Z,\-&’\.]*MINISTER[\sA-Z,\-&’\.]*'
    r'(?:\([A-Z\s\.]+\))?'
    r')'
    r')\s*:',
    re.MULTILINE
)


# =========================================================
# 4. SPEAKER NORMALIZATION
# =========================================================

def normalize_speaker(raw_speaker):

    speaker = raw_speaker.strip()

    if "SPEAKER" in speaker:
        return "HON_SPEAKER"

    if "SECRETARY" in speaker:
        return "SECRETARY_GENERAL"

    if speaker.startswith("THE"):
        paren_match = re.search(r'\(([A-Z\s\.]+)\)', speaker)
        if paren_match:
            name = paren_match.group(1)
            name = re.sub(r'^(SHRI|SHRIMATI|DR\.)\s+', '', name)
            return re.sub(r'\s+', ' ', name).strip()

    speaker = re.sub(r'\([^)]*\)', '', speaker)
    speaker = re.sub(r'^(SHRI|SHRIMATI|DR\.)\s+', '', speaker)
    speaker = re.sub(r'\s+', ' ', speaker).strip()

    return speaker


# =========================================================
# 5. SEGMENTATION
# =========================================================

def segment_speeches(text):

    matches = list(SPEAKER_PATTERN.finditer(text))
    speeches = []

    for i, match in enumerate(matches):

        raw_speaker = match.group("speaker").strip()
        normalized_speaker = normalize_speaker(raw_speaker)

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        speech_text = text[start:end].strip()

        speech_text = re.sub(r'\*+', '', speech_text)
        speech_text = re.sub(r'\d{1,2}\.\d{2}\s*hrs', '', speech_text, flags=re.IGNORECASE)
        speech_text = re.sub(r'\s+', ' ', speech_text).strip()

        if len(speech_text.split()) < 10:
            continue

        speeches.append({
            "raw_speaker": raw_speaker,
            "speaker": normalized_speaker,
            "speech_text": speech_text,
            "word_count": len(speech_text.split()),
            "char_count": len(speech_text)
        })

    return speeches


# =========================================================
# 6. BUILD JSON PER DEBATE
# =========================================================

def build_json(filepath):

    metadata = extract_metadata_from_filename(filepath)
    if metadata is None:
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    text = clean_global_text(text)
    speeches = segment_speeches(text)

    for idx, speech in enumerate(speeches):
        speech["speech_id"] = f"{metadata['debate_id']}_{idx+1:03d}"
        speech["speech_index"] = idx + 1
        speech["speaker_role"] = None
        speech["is_presiding_officer"] = speech["speaker"] == "HON_SPEAKER"

    metadata["speeches"] = speeches

    return metadata


# =========================================================
# 7. PROCESS LATEST 30 FILES
# =========================================================

def get_latest_30_files():

    files = [
        os.path.join(CLEANED_TEXT_DIR, f)
        for f in os.listdir(CLEANED_TEXT_DIR)
        if f.endswith(".txt")
    ]

    dated_files = []

    for f in files:
        meta = extract_metadata_from_filename(f)
        if meta:
            dated_files.append((f, meta["date"]))

    dated_files.sort(key=lambda x: x[1], reverse=True)

    return [f[0] for f in dated_files[:30]]


# =========================================================
# 8. RUN PIPELINE
# =========================================================

if __name__ == "__main__":

    latest_files = get_latest_30_files()

    all_rows = []

    for filepath in latest_files:

        debate_json = build_json(filepath)
        if debate_json is None:
            continue

        # Save per-debate JSON
        output_path = os.path.join(
            STRUCTURED_DIR,
            debate_json["debate_id"] + ".json"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(debate_json, f, indent=2, ensure_ascii=False)

        # Flatten for master dataset
        for speech in debate_json["speeches"]:
            row = speech.copy()
            row.update({
                "date": debate_json["date"],
                "year": debate_json["year"],
                "month": debate_json["month"],
                "lok_sabha_number": debate_json["lok_sabha_number"],
                "session_number": debate_json["session_number"],
                "debate_id": debate_json["debate_id"]
            })
            all_rows.append(row)

    # Master DataFrame for NER tagging
    master_df = pd.DataFrame(all_rows)

    master_df.to_csv(
        os.path.join(STRUCTURED_DIR, "lok_sabha_latest30_master.csv"),
        index=False
    )

    print("Structured JSON files saved.")
    print("Master dataset created for NER tagging.")
    print("Total speeches:", len(master_df))
    print("Unique speakers:", master_df["speaker"].nunique())
