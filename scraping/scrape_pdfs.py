import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time

BASE_URL = "https://eparlib.sansad.in"
BROWSE_URL = "https://eparlib.sansad.in/handle/123456789/2963706/browse?page-token=bf722ee33a0d&page-token-value=596fa82b59fcef0a91ef75a136cf68ed&type=date&sort_by=1&order=DESC&rpp=100&submit_browse=Update"

PDF_DIR = "data/raw_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)


headers = {
    "User-Agent": "Mozilla/5.0"
}


def get_view_links():
    print("Fetching browse page...")
    response = requests.get(BROWSE_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    view_links = []

    # Find table rows
    rows = soup.find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 4:
            view_cell = cols[3]  # 4th column = View
            link = view_cell.find("a", href=True)
            if link:
                href = link["href"]
                full_link = BASE_URL + href
                view_links.append(full_link)

    print(f"Found {len(view_links)} view pages.")
    return view_links


def get_pdf_link(view_url):
    try:
        response = requests.get(view_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/bitstream/" in href and href.endswith(".pdf"):
                return BASE_URL + href
    except Exception as e:
        print(f"Error accessing {view_url}: {e}")

    return None


def download_pdf(pdf_url):
    filename = pdf_url.split("/")[-1]
    filepath = os.path.join(PDF_DIR, filename)

    if os.path.exists(filepath):
        return

    try:
        response = requests.get(pdf_url, headers=headers, stream=True)
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    except Exception as e:
        print(f"Error downloading {pdf_url}: {e}")


if __name__ == "__main__":

    view_links = get_view_links()

    for view_url in tqdm(view_links):
        pdf_url = get_pdf_link(view_url)

        if pdf_url:
            download_pdf(pdf_url)

        time.sleep(1)  # polite delay

    print("All downloads complete.")
