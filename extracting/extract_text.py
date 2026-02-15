import os
import pdfplumber
from tqdm import tqdm

PDF_DIR = "data/raw_pdfs"
TEXT_DIR = "data/raw_text"

os.makedirs(TEXT_DIR, exist_ok=True)


def extract_pdf_text(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text


if __name__ == "__main__":
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    for pdf_file in tqdm(pdf_files):
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        text = extract_pdf_text(pdf_path)

        text_filename = pdf_file.replace(".pdf", ".txt")
        text_path = os.path.join(TEXT_DIR, text_filename)

        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

    print("Text extraction complete.")
