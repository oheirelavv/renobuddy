# RenoBuddy

A RAG-powered Streamlit application that helps Singapore HDB homeowners navigate renovations using official government sources.

## Features

- **Plan My Reno** — Personalised renovation plan and interactive checklist
- **Verify the Advice** — Check contractor or ID claims against official sources
- **Ask RenoBuddy** — Conversational Q&A with citations
- **Manage Knowledge Base** — Admin-only source management (requires admin login)

## Quick Start (Local)

### 1. Clone and install

```bash
cd renobuddy
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up credentials

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
python setup_auth.py
# Follow prompts to create admin and user accounts
```

### 3. Run the app

```bash
streamlit run app/Home.py
```

The app opens at `http://localhost:8501`.

## Deployment (Streamlit Community Cloud)

### 1. Push to GitHub

```bash
git init
git add -A
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/renobuddy.git
git push -u origin main
```

### 2. Create the app on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select your `renobuddy` repository, branch `main`, and set the main file path to `app/Home.py`.

### 3. Add Secrets

In the Streamlit Cloud dashboard, go to **Settings > Secrets** and paste the following (replace placeholders with real values):

```toml
OPENAI_API_KEY = "sk-..."

[auth]
admin_username = "admin"
admin_password_hash = "PASTE_HASH_FROM_setup_auth.py"
user_username = "user"
user_password_hash = "PASTE_HASH_FROM_setup_auth.py"
```

To generate password hashes locally, run `python setup_auth.py` and copy the hashes from `.streamlit/secrets.toml`.

### 4. Deploy

Click **Deploy**. The app will install dependencies from `requirements.txt` and start.

### Important notes

- **ChromaDB and embeddings** are pre-built and committed in `data/chroma_db/` and `data/processed/`. No embedding API calls are needed at startup.
- **Admin ingestion** (adding new sources via Manage Knowledge Base) writes to ephemeral storage on Streamlit Cloud. Newly added sources are lost on redeployment. To persist them, commit the updated data files to your repository.
- **Secrets** are never committed to the repository. The `.gitignore` excludes `.env` and `.streamlit/secrets.toml`.

## Data Sources

- Housing & Development Board (HDB) — 7 official sources
- Singapore Civil Defence Force (SCDF) — 1 official source
- Qanvast — 4 supplementary third-party sources

## Architecture

- **LLM**: GPT-4.1-mini (OpenAI)
- **Embeddings**: text-embedding-3-small
- **Vector DB**: ChromaDB (persistent, local)
- **Frontend**: Streamlit
- **Knowledge base**: 95 chunks from 11 sources
