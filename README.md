# NEET PG Clinical Vignette Dashboard

A role-based Streamlit dashboard for NEET PG preparation with admin quiz generation, draft/publish workflow, public quiz links, mandatory candidate registration, +4/-1 scoring, and mnemonic feedback for incorrect answers.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure admin and Clerk credentials through Streamlit secrets. For local development, create `.streamlit/secrets.toml`:

```toml
ADMIN_PASSWORD = "replace-with-a-strong-admin-password"
ADMIN_EMAIL = "admin@example.com"

[clerk]
client_id = "your-clerk-oauth-client-id"
client_secret = "your-clerk-oauth-client-secret"
redirect_uri = "http://localhost:8501"
fapi_url = "https://your-clerk-frontend-api.clerk.accounts.dev"
```

For Clerk, use the OAuth/OIDC application credentials from Clerk Dashboard. The `client_secret` is the OAuth application client secret, not the Clerk `sk_test_...` or `sk_live_...` API secret.

You can also configure Gemini through Streamlit secrets:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
GEMINI_MODEL = "gemini-3.5-flash"
```

Environment variables are also supported for local development:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GEMINI_MODEL="gemini-3.5-flash"
export ADMIN_PASSWORD="replace-with-a-strong-admin-password"
export ADMIN_EMAIL="admin@example.com"
export CLERK_CLIENT_ID="your-clerk-oauth-client-id"
export CLERK_CLIENT_SECRET="your-clerk-oauth-client-secret"
export CLERK_REDIRECT_URI="http://localhost:8501"
export CLERK_FAPI_URL="https://your-clerk-frontend-api.clerk.accounts.dev"
```

If no Gemini key is configured, the dashboard still runs, but admins must add published quizzes before candidates can attempt a test.

## Run

```bash
streamlit run app.py
```

Use `?view=admin` for admin login and `?view=public` for the public quiz portal.

## Change Admin Password

Set `ADMIN_PASSWORD` in `.streamlit/secrets.toml` for local development. For Streamlit Cloud, set the same key in **App settings → Secrets** and redeploy/reboot the app.

Do not commit real passwords, Clerk secrets, or Gemini keys. Keep `.streamlit/secrets.toml` and `.env` local only.

## Deploy To Streamlit Cloud

1. Push this repository to GitHub.
2. In Streamlit Cloud, click **New app** and choose the repository, branch, and `app.py` as the main file.
3. Open **Advanced settings → Secrets** and paste:

```toml
ADMIN_PASSWORD = "replace-with-a-strong-admin-password"
ADMIN_EMAIL = "admin@example.com"
GEMINI_API_KEY = "your-gemini-api-key"
GEMINI_MODEL = "gemini-3.5-flash"

[clerk]
client_id = "your-clerk-oauth-client-id"
client_secret = "your-clerk-oauth-client-secret"
redirect_uri = "https://your-streamlit-app.streamlit.app"
fapi_url = "https://your-clerk-frontend-api.clerk.accounts.dev"
```

4. In Clerk Dashboard, add the deployed Streamlit URL as an allowed redirect URI for the same OAuth/OIDC application:

```text
https://your-streamlit-app.streamlit.app
```

5. Deploy the app, then test sign-in and `?view=admin`.

## Gemini Prompt Strategy

The app sends Gemini a strict JSON prompt that requires Google Search grounding before item writing, limits questions to Medium and Hard difficulty, asks for long NEET PG-style clinical stems, and requires diagram/investigation-style questions through `visual_type` and `diagram_prompt` fields.

A copy-ready standalone version is available in `GEMINI_PROMPT.md`.

The admin selects one or more NEET PG subjects from the complete subject list, chooses the question count, and saves the generated quiz as either `draft` or `published`. Public candidates only see published quizzes.

Admins generate questions from the `Quiz Creator` page by selecting subjects, choosing the question count, selecting draft/published status, and clicking `Generate with Gemini`.

The prompt also asks Gemini to balance selected subjects, include plausible distractors, avoid obsolete low-yield trivia, and provide a memory tip for every generated item so missed questions can produce targeted revision anchors.