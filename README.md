# AI Knowledge Assistant

## Run locally on Windows

Open two PowerShell terminals in the project root (`D:\AI-Knowledge-Assistant`).

Install dependencies once:

```powershell
python -m pip install -r requirements.txt
```

Documents are split into overlapping, paragraph-aware 1,000-character chunks
(200 characters of overlap), embedded with the Hugging Face Inference Providers
`BAAI/bge-small-en-v1.5` embedding API, and stored in FAISS. This avoids loading
a local ML model or PyTorch in the backend. The same hosted model embeds document
chunks and questions. Answers are generated through the Hugging Face Hub
Inference API using only retrieved document passages; each answer includes its
source passages. The retrieval score cutoff defaults to `0.45` for this
embedding model; `RAG_MIN_SCORE` can override it for a different corpus.

After switching from SentenceTransformer embeddings, the existing FAISS index
is not used: its `chunks.json` has no embedding identity, so the backend starts
without loading that index until all uploaded documents are re-indexed. The
re-index operation rebuilds `vector_data/index.faiss` and
`vector_data/chunks.json` with the new embedding API.

Configure the Hugging Face Hub token used by the LLM:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set `HF_TOKEN` to a Hugging Face access token permitted to use
the Inference Providers for both `BAAI/bge-small-en-v1.5` embeddings and the
configured chat model. No separate embedding token is required. Provider access
or usage may be subject to your Hugging Face account's available credits.
The default chat model is `openai/gpt-oss-120b`; set `AI_MODEL` to another
chat-completion model available to your account if needed. Do not commit `.env`.

In the first terminal, start the API:

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

In the second terminal, start Streamlit:

```powershell
streamlit run frontend/app.py
```

Open <http://localhost:8501>. The API health endpoint is
<http://127.0.0.1:8000/health>.

### Rebuild and verify the knowledge base locally

In PowerShell, once the API is running, rebuild the full index from the
documents already in `uploads` (the endpoint rebuilds every supported file):

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents/TASK%203%20REPORT.pdf/reindex"
```

To upload an additional local document (replace the path with a supported
PDF, DOCX, or TXT file):

```powershell
curl.exe -F "file=@.\path\to\document.pdf" http://127.0.0.1:8000/upload
```

Re-index the uploaded file (which rebuilds the complete index), then inspect
retrieval and returned source names:

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe -X POST "http://127.0.0.1:8000/documents/document.pdf/reindex"
curl.exe http://127.0.0.1:8000/documents

$body = @{ question = "What happened in Task 3?" } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ask" -ContentType "application/json" -Body $body

$body = @{ question = "What happened in Task 4?" } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ask" -ContentType "application/json" -Body $body

$body = @{
    question = "Compare both documents"
    recent_questions = @("Tell me about Task 3 report", "Tell me about Task 4 report")
} | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ask" -ContentType "application/json" -Body $body

$body = @{ question = "What documents are uploaded?" } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ask" -ContentType "application/json" -Body $body

$body = @{ question = "What is the capital of Atlantis?" } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ask" -ContentType "application/json" -Body $body
```

For the Task 3, Task 4, multi-document, inventory, and out-of-scope requests,
the answer and `sources` should reflect the indexed documents; inventory and
out-of-scope responses do not require an LLM answer call.

If the commands are not found, activate the project virtual environment in
each terminal before running them:

```powershell
.\venv\Scripts\Activate.ps1
```

## Deployment configuration

This repository includes a Render Blueprint in [render.yaml](./render.yaml).
Create a new Blueprint from the GitHub repository and Render will provision
the FastAPI backend and Streamlit frontend as separate free web services.
During initial setup, provide `HF_TOKEN` securely in Render's prompt; do not
put the token in the Blueprint or commit it to the repository. The frontend
gets the backend hostname from the Blueprint.
`HF_TOKEN` is used for both embeddings and answer generation; no other
embedding-specific environment variable is required. The backend's startup
does not download a model. After documents are uploaded, call the re-index
endpoint for one uploaded filename to rebuild the full FAISS index before
asking document-content questions.

### Host the UI on Streamlit Community Cloud

The Streamlit UI can instead be hosted on Streamlit Community Cloud while the
FastAPI backend remains on Render:

1. Deploy the FastAPI service from the Render Blueprint and wait for its
   `/health` endpoint to respond successfully.
2. In Streamlit Community Cloud, create an app from this repository's `main`
   branch and set the app file to `frontend/app.py`.
3. In the app's **Settings → Secrets**, set the backend URL:

   ```toml
   API_URL = "https://ai-knowledge-assistant-api-npde.onrender.com"
   ```

   `API_URL` is not a credential, but Streamlit Secrets provides a convenient
   way to configure it. The app also accepts `API_URL` from the environment;
   local development continues to use `.env`.
4. Streamlit Cloud installs the UI-only dependencies from
   [frontend/requirements.txt](./frontend/requirements.txt). The backend's
   dependencies remain in the root `requirements.txt` for Render.

The Streamlit UI depends on the Render API being reachable. Free Render
services can spin down when idle, so the first request may take time. Uploaded
documents and the FAISS index are stored by the backend and can be lost when
its ephemeral storage is cleared; re-upload and index documents afterward.
