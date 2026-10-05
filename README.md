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

This repository includes a Render Blueprint in [render.yaml](./render.yaml).
Create a new Blueprint from the GitHub repository and Render will provision
the FastAPI backend and Streamlit frontend as separate free web services.
During initial setup, provide `HF_TOKEN` securely in Render's prompt; do not
put the token in the Blueprint or commit it to the repository. The frontend
gets the backend hostname from the Blueprint.

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
