PDF Parsing pipeline

This small utility provides a robust PDF parsing pipeline with:

- Layout-aware extraction using pdfplumber
- Unicode and embedded font handling via PyMuPDF (fitz)
- OCR fallback using Tesseract (via pdf2image + pytesseract) for scanned pages
- Encoding validation and chunk quality checks (entropy, symbol ratio, repetitiveness)
- CLI preview to accept/reject chunks before embedding

Installation (Windows):

1. Install Python 3.10+ and create a virtualenv
2. Install Tesseract OCR and add it to PATH (https://github.com/tesseract-ocr/tesseract)
	- On Windows, download the installer and ensure the installation path (e.g., C:\Program Files\Tesseract-OCR) is added to your PATH. You may need to set TESSDATA_PREFIX if language data is in a custom location.
3. From workspace root:

```powershell
python -m venv .venv; .venv\Scripts\Activate; pip install -r requirements.txt
```

Usage example:

```powershell
python -m src.pdf_parser parse "mydoc.pdf" --preview

During preview the script will show parsed chunks and prompt you to keep or discard each chunk. Kept chunks are marked with a `keep` flag in the JSON output.
```

Notes:
- This is scaffolding and unit tests for the quality checks are included. Run `pytest` to run tests.
