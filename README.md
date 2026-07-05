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

Environment variables are also supported for local development:

```bash
export ADMIN_PASSWORD="replace-with-a-strong-admin-password"
export ADMIN_EMAIL="admin@example.com"
export CLERK_CLIENT_ID="your-clerk-oauth-client-id"
export CLERK_CLIENT_SECRET="your-clerk-oauth-client-secret"
export CLERK_REDIRECT_URI="http://localhost:8501"
export CLERK_FAPI_URL="https://your-clerk-frontend-api.clerk.accounts.dev"
```

## Run

```bash
streamlit run app.py
```

Use `?view=admin` for admin login and `?view=public` for the public quiz portal.

## Change Admin Password

Set `ADMIN_PASSWORD` in `.streamlit/secrets.toml` for local development. For Streamlit Cloud, set the same key in **App settings → Secrets** and redeploy/reboot the app.

Do not commit real passwords or Clerk secrets. Keep `.streamlit/secrets.toml` and `.env` local only.

## Deploy To Streamlit Cloud

1. Push this repository to GitHub.
2. In Streamlit Cloud, click **New app** and choose the repository, branch, and `app.py` as the main file.
3. Open **Advanced settings → Secrets** and paste:

```toml
ADMIN_PASSWORD = "replace-with-a-strong-admin-password"
ADMIN_EMAIL = "admin@example.com"

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