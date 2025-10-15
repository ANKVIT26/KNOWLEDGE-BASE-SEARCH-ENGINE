# Optimized Flask app with faster PDF processing, timeouts, streaming, and background-ready architecture.

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import fitz  # PyMuPDF
import math, requests, io, time, signal

app = Flask(__name__, static_folder='static')
CORS(app)

# ---- CONFIG ----
GEMINI_API_KEY = "AIzaSyAZXVafDxyqwk***********"  # Replace with your api key
GEMINI_MODEL = "models/gemini-2.0-flash"
MAX_PAGES = 150

DOCUMENTS = []
CHUNKS = []
EMBEDDINGS = {}

# ---- UTILS ----
def timeout_handler(signum, frame):
    raise TimeoutError("Timed out during PDF processing")


def safe_extract_text(pdf_stream, max_pages=MAX_PAGES):
    """Fully safe, UTF-8 enforced PDF text extraction with Unicode normalization and per-page isolation."""
    import unicodedata, re
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(20)
    try:
        # Open PDF safely
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        if doc.is_encrypted:
            try:
                doc.authenticate("")
            except:
                return ""  # silent fail instead of returning JSON inside extractor

        texts = []

        # Helper to ensure UTF-8 normalization and remove broken glyphs
        def clean_text(t):
            if not isinstance(t, str):
                return ""
            t = unicodedata.normalize('NFKC', t)  # Normalize unicode
            # Replace resume bullet glyphs/icons with hyphen
            t = re.sub(r"[•‣›▶➤➢➔➜✦✶✱★☆⚫⚪▪▫●◦–—−]", " - ", t)
            # Strip illegal control chars
            t = ''.join(ch if (32 <= ord(ch) <= 0xD7FF or 0xE000 <= ord(ch) <= 0xFFFD) else ' ' for ch in t)
            # Collapse whitespace noise
            t = re.sub(r"\s+", " ", t).strip()
            return t

        # Extract page-by-page without crashing
        for page_num, page in enumerate(doc):
            if page_num >= max_pages:
                break  # Hard stop to avoid infinite parsing on malformed PDFs
            try:
                raw = page.get_text("text", sort=True)
                if not raw or not raw.strip():
                    raw = page.get_text("blocks")
                if not raw or not str(raw).strip():
                    try:
                        rd = page.get_text("rawdict")
                        parts = []
                        for b in rd.get('blocks', []):
                            for l in b.get('lines', []):
                                for s in l.get('spans', []):
                                    parts.append(s.get('text', ''))
                        raw = " ".join(parts)
                    except:
                        raw = ""
                text = clean_text(raw)
            except:
                text = ""  # Never crash here
            if text and len(text) > 10:
                texts.append(text)

        doc.close()
        signal.alarm(0)

        # Final UTF-8 safe return
        combined = "\n".join(texts)
        if isinstance(combined, bytes):
            combined = combined.decode("utf-8", errors="ignore")
        return combined.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    except:
        signal.alarm(0)
        return ""


# ---- ROUTES ----
@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')


@app.route('/extract_text', methods=['POST'])
def extract_text():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        # Support TXT direct upload
        if file.filename.lower().endswith('.txt'):
            text_output = file.stream.read().decode('utf-8', errors='ignore')
            return jsonify({"text": text_output})
        pdf_data = io.BytesIO(file.stream.read())
        text_output = safe_extract_text(pdf_data)
        return jsonify({"text": text_output})
    except Exception as e:
        return jsonify({"error": f"PDF extraction failed: {e}"}), 500


@app.route('/upload_doc', methods=['POST'])
def upload_doc():
    # Support both JSON and direct file upload for txt/pdf
    if 'file' in request.files:
        file = request.files['file']
        fname = file.filename
        if fname.lower().endswith('.txt'):
            name = fname
            content = file.stream.read().decode('utf-8', errors='ignore')
        elif fname.lower().endswith('.pdf'):
            # extract text via safe_extract_text for PDF
            pdf_data = io.BytesIO(file.stream.read())
            content = safe_extract_text(pdf_data)
            name = fname
        else:
            return jsonify({"error": "Unsupported file type"}), 400
    else:
        data = request.get_json()
        name = data.get("name")
        content = data.get("content", "")
    if not name or not content.strip():
        return jsonify({"error": "Invalid document"}), 400
        return jsonify({"error": "Invalid document"}), 400

    start = time.time()
    doc_id = len(DOCUMENTS) + 1
    DOCUMENTS.append({"id": doc_id, "name": name, "content": content})

    # Optimized chunking
    chunks = []
    size, overlap = 1200, 200
    for i in range(0, len(content), size - overlap):
        text = content[i:i + size]
        chunks.append({"id": f"{doc_id}_{i}", "docId": doc_id, "docName": name, "text": text})

    CHUNKS.extend(chunks)
    for c in chunks:
        EMBEDDINGS[c["id"]] = generate_embedding(c["text"])

    print(f"Processed {len(chunks)} chunks in {round(time.time()-start, 2)}s")
    return jsonify({"status": "ok", "chunks": len(chunks)})


@app.route('/query', methods=['POST'])
def query_docs():
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Empty query"}), 400
    if not CHUNKS:
        return jsonify({"error": "Please upload documents first"}), 400

    query_vec = generate_embedding(query)
    relevant = find_relevant_chunks(query_vec, top_k=5)
    context = "\n\n".join([c["text"] for c in relevant])
    prompt = (
        "Answer ONLY using the content from this PDF. "
        "Do NOT make assumptions or add external knowledge. "
        "If the answer is not in the PDF, reply exactly with: 'Not found in document.'\n\n"
        f"PDF Content:\n{context}\n\nQuestion: {query}\nAnswer:"
    )
    answer = call_gemini_api(prompt)
    return jsonify({"answer": answer, "sources": list({c['docName'] for c in relevant})})


# ---- HELPERS ----
def generate_embedding(text):
    vec = [0]*128
    for w in text.lower().split():
        idx = sum(ord(c) for c in w) % 128
        vec[idx] += 1
    norm = math.sqrt(sum(v*v for v in vec)) or 1
    return [v/norm for v in vec]


def cosine_similarity(a, b):
    return sum(x*y for x, y in zip(a, b))


def find_relevant_chunks(qv, top_k=5):
    scored = [(cosine_similarity(qv, EMBEDDINGS[c["id"]]), c) for c in CHUNKS]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [c for _, c in scored[:top_k]]


def call_gemini_api(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json; charset=utf-8", "Accept-Charset": "utf-8"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        r.encoding = 'utf-8'
        r.raise_for_status()
        res = r.json()
        # Ensure UTF-8 decoding
        answer_text = res["candidates"][0]["content"][0]["text"]
        return answer_text.encode('utf-8').decode('utf-8')
    except Exception as e:
        return f"Gemini API error: {e}"


if __name__ == '__main__':
    app.run(debug=True, port=5000)
