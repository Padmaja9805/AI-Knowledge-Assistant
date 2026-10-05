# AI Knowledge Assistant

## Run locally on Windows

Open two PowerShell terminals in the project root (`D:\AI-Knowledge-Assistant`).

Install dependencies once:

```powershell
python -m pip install -r requirements.txt
```

Documents are split into overlapping, paragraph-aware 1,000-character chunks
(200 characters of overlap), embedded, and stored in FAISS. Answers are
generated through the Hugging Face Hub Inference API using only retrieved
document passages; each answer includes its source passages.

After upgrading an existing installation, open **Documents** and choose
**Reindex** so previously uploaded files are rebuilt using the new chunk
settings.

Configure the Hugging Face Hub token used by the LLM:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set `HF_TOKEN` to your Hugging Face access token. The default
model is `openai/gpt-oss-120b`; set `AI_MODEL` to another chat-completion model
available to your Hugging Face account if needed. Do not commit `.env`.

In the first terminal, start the API:

```powershell
uvicorn backend.main:app --reload
```

In the second terminal, start Streamlit:

```powershell
streamlit run frontend/app.py
```

Open <http://localhost:8501>. The API health endpoint is
<http://127.0.0.1:8000/health>.

If the commands are not found, activate the project virtual environment in
each terminal before running them:

```powershell
.\venv\Scripts\Activate.ps1
```

## Deployment configuration

Deploy the FastAPI backend and Streamlit frontend as separate web services.
Set `HF_TOKEN` on the backend and set `API_URL` on the frontend to the
backend's public base URL (for example, `https://your-api.example.com`, without
an `/ask` suffix). Keep the deployed service start commands separate:

```text
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port $PORT
```

Configure persistent storage for `uploads/` and `vector_data/` on the backend
host. Without persistent storage, files and the index can be lost when the
service restarts or is redeployed.
