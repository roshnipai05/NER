import re
import json
import os
import unicodedata
from datetime import datetime
import pandas as pd


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
        lok_sabha_number = None
        session_number = None
        date_obj = None
        date_str = None

    return {
        "debate_id": f"{lok_sabha_number}_{session_number}_{date_str}" if date_str else None,
        "date": date_obj.strftime("%Y-%m-%d") if date_obj else None,
        "year": date_obj.year if date_obj else None,
        "month": date_obj.month if date_obj else None,
        "lok_sabha_number": lok_sabha_number,
        "session_number": session_number,
        "source_file": filename
    }


# =========================================================
# 2. GLOBAL CLEANING (WITH ENCODING FIX)
# =========================================================

def clean_global_text(text):

    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)

    # Remove common PDF artifacts
    text = re.sub(r'[�]', '', text)
    text = re.sub(r'\u200b', '', text)
    text = re.sub(r'\xa0', ' ', text)

    # Remove footer lines safely (no truncation)
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
    r'(HON\. SPEAKER|SECRETARY[- ]GENERAL|'
    r'(SHRI|SHRIMATI|DR\.)\s+[A-Z][A-Z\s\.\-\(\)]*|'
    r'THE MINISTER OF [A-Z ,;\-\(\)]*'
    r'(?:\n\([A-Z\s\.]+\))?'
    r')'
    r')\s*:',
    re.MULTILINE
)


# =========================================================
# 4. SPEAKER NORMALIZATION
# =========================================================

def normalize_speaker(raw_speaker):

    speaker = raw_speaker.strip()

    # -------------------------------------------------
    # 1. Presiding officers
    # -------------------------------------------------
    if "SPEAKER" in speaker:
        return "HON_SPEAKER"

    if "SECRETARY" in speaker:
        return "SECRETARY_GENERAL"

    # -------------------------------------------------
    # 2. Minister format
    # Example:
    # THE MINISTER OF FINANCE ... (SHRIMATI NIRMALA SITHARAMAN)
    # -------------------------------------------------
    if speaker.startswith("THE MINISTER OF"):

        paren_match = re.search(r'\(([A-Z\s\.]+)\)', speaker)
        if paren_match:
            name = paren_match.group(1)
            name = re.sub(r'^(SHRI|SHRIMATI|DR\.)\s+', '', name)
            return name.strip()

    # -------------------------------------------------
    # 3. Regular MP format
    # Example:
    # SHRI VINOD KUMAR SONKAR (KAUSHAMBI)
    # -------------------------------------------------

    # Remove constituency
    speaker = re.sub(r'\(.*?\)', '', speaker)

    # Remove titles
    speaker = re.sub(r'^(SHRI|SHRIMATI|DR\.)\s+', '', speaker)

    speaker = speaker.strip()

    return speaker


# =========================================================
# 5. SPEECH SEGMENTATION
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

        # Remove interruptions
        speech_text = re.sub(
            r'\(.*?Interrupt.*?\)',
            '',
            speech_text,
            flags=re.IGNORECASE
        )

        # Remove stray footnote stars
        speech_text = re.sub(r'\*+', '', speech_text)

        # Remove time markers
        speech_text = re.sub(
            r'\d{1,2}\.\d{2}\s*hrs',
            '',
            speech_text,
            flags=re.IGNORECASE
        )

        # Collapse whitespace
        speech_text = re.sub(r'\s+', ' ', speech_text).strip()

        if len(speech_text) < 30:
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
# 6. BUILD JSON
# =========================================================

def build_json(filepath):

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    metadata = extract_metadata_from_filename(filepath)
    text = clean_global_text(text)

    speeches = segment_speeches(text)

    for idx, speech in enumerate(speeches):
        speech["speech_id"] = f"{metadata['debate_id']}_{idx+1:03d}"
        speech["speaker_role"] = None
        speech["is_presiding_officer"] = speech["speaker"] == "HON_SPEAKER"

    metadata["speeches"] = speeches

    return metadata


# =========================================================
# 7. JSON → DATAFRAME
# =========================================================

def json_to_dataframe(json_data):
    df = pd.DataFrame(json_data["speeches"])

    df["date"] = json_data["date"]
    df["year"] = json_data["year"]
    df["month"] = json_data["month"]
    df["lok_sabha_number"] = json_data["lok_sabha_number"]
    df["session_number"] = json_data["session_number"]

    return df


# =========================================================
# 8. RUN
# =========================================================

if __name__ == "__main__":

    filepath = "data/cleaned_text/lsd_17_6_04-08-2021_eng_editorial.txt"

    debate_json = build_json(filepath)

    with open("segmented_debate.json", "w", encoding="utf-8") as f:
        json.dump(debate_json, f, indent=4, ensure_ascii=False)

    df = json_to_dataframe(debate_json)
    
    def display_full_debate(df): 
        for _, row in df.iterrows(): 
            print("="*100) 
            print(f"SPEECH ID: {row['speech_id']}") 
            print(f"SPEAKER: {row['speaker']}") 
            print(f"WORD COUNT: {row['word_count']}") 	
            print("-"*100) 
            print(row['speech_text']) 
            print("\n")
            
    display_full_debate(df)

    print("Unique Canonical Speakers:", df["speaker"].nunique())
    
    print("\n=== UNIQUE SPEAKERS ===")
    for s in sorted(df["speaker"].unique()):
        print(s)

    print("\n=== SPEAKER FREQUENCY ===")
    print(df["speaker"].value_counts())

    print("\n=== RAW → NORMALIZED ===")
    print(df[["raw_speaker", "speaker"]].drop_duplicates())
    
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
        print("Raw length:", len(raw))
        cleaned = clean_global_text(raw)
        print("After cleaning length:", len(cleaned))
    


