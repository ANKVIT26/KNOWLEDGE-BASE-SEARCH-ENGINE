PDF Parsing pipeline

This small utility provides a robust PDF parsing pipeline with:

- Layout-aware extraction using pdfplumber
- Unicode and embedded font handling via PyMuPDF (fitz)
- OCR fallback using Tesseract (via pdf2image + pytesseract) for scanned pages
- Encoding validation and chunk quality checks (entropy, symbol ratio, repetitiveness)
- CLI preview to accept/reject chunks before embedding

Installation

1. Clone the repository (replace the URL with your repo):

```bash
git clone https://github.com/ANKVIT26/KNOWLEDGE-BASE-SEARCH-ENGINE.git
cd KNOWLEDGE-BASE-SEARCH-ENGINE
```

If the link fails, common causes and fixes:

- Check the repository name and casing — GitHub repo names are case-sensitive in URLs. Confirm the correct URL on GitHub.
- If the repository is private, make sure you have access and are authenticated (use a personal access token or SSH key).
- Try the SSH clone if you have an SSH key configured:

```bash
git clone git@github.com:ANKVIT26/KNOWLEDGE-BASE-SEARCH-ENGINE.git
```

- If you still see errors, run:

```bash
# show detailed git clone output
GIT_TRACE=1 GIT_CURL_VERBOSE=1 git clone https://github.com/ANKVIT26/knowledge-base-rag.git
```

On Windows PowerShell, set the env vars like this before running the command:

```powershell
$env:GIT_TRACE = 1
$env:GIT_CURL_VERBOSE = 1
git clone https://github.com/ANKVIT26/knowledge-base-rag.git
```

2. Install Python 3.10+ (3.11 recommended). Setup virtualenv and install dependencies.

Bash / macOS / WSL:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

PowerShell (Windows):

```powershell
python -m venv .venv
. .venv\Scripts\Activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
```

3. Install Tesseract OCR and add it to PATH (https://github.com/tesseract-ocr/tesseract)
   - On Windows, download the installer and ensure the installation path (e.g., C:\Program Files\Tesseract-OCR) is added to your PATH. You may need to set TESSDATA_PREFIX if language data is in a custom location.

Usage example:

```powershell
python -m src.pdf_parser parse "mydoc.pdf" --preview

During preview the script will show parsed chunks and prompt you to keep or discard each chunk. Kept chunks are marked with a `keep` flag in the JSON output.
```

Notes:
- This is scaffolding and unit tests for the quality checks are included. Run `pytest` to run tests.
