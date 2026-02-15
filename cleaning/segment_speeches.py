import re
import json
import os
from datetime import datetime
import pandas as pd


# ------------------------------
# 1. Metadata extraction
# ------------------------------

def extract_metadata_from_filename(filepath):
    filename = os.path.basename(filepath)

    # Example: lsd_17_5_29-01-2021_eng_editorial.txt
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


# ------------------------------
# 2. Remove front matter
# ------------------------------

def remove_front_matter(text):
    # Debate usually begins when actual proceedings start
    start_pattern = r"LOK SABHA\s*-+\s*Friday"
    match = re.search(start_pattern, text)

    if match:
        return text[match.start():]
    else:
        return text


# ------------------------------
# 3. Identify speaker markers
# ------------------------------

SPEAKER_PATTERN = re.compile(
    r'^(HON\. SPEAKER|SHRI|SHRIMATI|DR\.|SECRETARY-GENERAL|THE MINISTER OF.*?)[:\-]',
    re.MULTILINE
)


def segment_speeches(text):
    matches = list(SPEAKER_PATTERN.finditer(text))

    speeches = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        speech_block = text[start:end].strip()

        # Extract speaker line
        first_line = speech_block.split('\n')[0]

        # Clean speaker name
        speaker = re.sub(r'[:\-]', '', first_line).strip()

        # Extract speech text (remove first line)
        speech_text = '\n'.join(speech_block.split('\n')[1:]).strip()

        # Remove interruptions
        speech_text = re.sub(r'\(Interruptions.*?\)', '', speech_text)
        speech_text = re.sub(r'\*.*?\*', '', speech_text)

        speech_text = re.sub(r'\s+', ' ', speech_text).strip()

        if len(speech_text) < 20:
            continue  # discard trivial segments

        speeches.append({
            "speaker": speaker,
            "speech_text": speech_text,
            "word_count": len(speech_text.split()),
            "char_count": len(speech_text)
        })

    return speeches


# ------------------------------
# 4. Build JSON structure
# ------------------------------

def build_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    metadata = extract_metadata_from_filename(filepath)

    text = remove_front_matter(text)

    speeches = segment_speeches(text)

    # Add speech IDs
    for idx, speech in enumerate(speeches):
        speech["speech_id"] = f"{metadata['debate_id']}_{idx+1:03d}"
        speech["speaker_role"] = None
        speech["is_presiding_officer"] = "SPEAKER" in speech["speaker"]

    metadata["speeches"] = speeches

    return metadata


# ------------------------------
# 5. Convert JSON to DataFrame
# ------------------------------

def json_to_dataframe(json_data):
    df = pd.DataFrame(json_data["speeches"])
    df["date"] = json_data["date"]
    df["year"] = json_data["year"]
    df["month"] = json_data["month"]
    df["lok_sabha_number"] = json_data["lok_sabha_number"]
    df["session_number"] = json_data["session_number"]
    return df


# ------------------------------
# 6. Example usage
# ------------------------------

filepath = "/mnt/data/lsd_17_5_29-01-2021_eng_editorial.txt"

debate_json = build_json(filepath)

# Save JSON
with open("segmented_debate.json", "w", encoding="utf-8") as f:
    json.dump(debate_json, f, indent=4, ensure_ascii=False)

# Convert to DataFrame
df = json_to_dataframe(debate_json)

print(df.head())
