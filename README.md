# Market Basket AI

A Flask dashboard for CSV exploration, charts, linear trend forecasts, rule-based suggestions, and optional AI advice. Requires Python 3.12.

## Run locally

From the project directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

Open http://127.0.0.1:5000. On macOS/Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python`.

Upload a CSV with a header and at least one numeric column. Forecasting needs at least three numeric observations and treats row order as time order. Uploads are limited to 16 MB and stored locally under `instance/uploads/`.

## Configuration

`.env.example` documents the settings; the application does **not** automatically load `.env` files. Set values in your shell or your host's environment settings. For example:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:FLASK_DEBUG = "false"
```

Save the generated secret in your hosting environment and reuse it across restarts. Local development can run without it, but sessions then reset when the application restarts. Set `FLASK_DEBUG=1` only during local development.

The default AI provider is local Ollama. Install Ollama, download a model with `ollama pull llama3.2:3b`, and ensure Ollama is running. The application falls back to built-in rules if the provider is unavailable.

The existing hosted provider option uses `AI_PROVIDER=openai` with `OPENAI_API_KEY`, and optional `OPENAI_BASE_URL` and `OPENAI_MODEL`. Keep credentials in the environment. The advisor sends column names, numeric summaries, top category values/counts, and your question to the configured provider. Category labels and questions may contain sensitive information even though complete CSV rows are not sent.

## Checks

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Tests use temporary uploads and mock AI requests, so no API key or running model is required. GitHub Actions runs the checks on pushes and pull requests.

## Publish to GitHub

Create an empty GitHub repository without an initial README or license. This project includes `.gitignore` rules for secrets, uploads, Python environments, and generated files. Review the files before committing:

```powershell
git status --short
git add .
git diff --cached --stat
git commit -m "Prepare Market Basket AI for GitHub"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the URL with your repository URL. If working from a downloaded copy without Git initialized, run `git init -b main` first. Choose a license before offering the project under open-source terms; none has been selected for you.

## Run on a Python host

GitHub stores the source code. [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) serves static sites and cannot run this Flask backend.

Configure a Python 3.12 web service connected to your repository:

- Install command: `python -m pip install -r requirements.txt`
- Start command: `python serve.py`
- Required environment: a persistent random `SECRET_KEY`
- Port: the host's `PORT` value, defaulting to `8000`
- Set `SESSION_COOKIE_SECURE=true` when serving over HTTPS.

`serve.py` runs Waitress and refuses to start without a secret. The host must provide a writable `instance/` directory. Use a single application instance because uploads are local files; ephemeral hosting storage loses them on redeployment. Localhost Ollama on the host refers to the host itself, not your laptop.

This app has no account authentication or automatic expiry for abandoned uploads. Restrict access for private use and arrange upload retention before a public rollout. Serve behind HTTPS. Reports include the first five uploaded rows. Charts load Chart.js from an external CDN.

## Project layout

- `app.py`: Flask routes, uploads, sessions, and reports
- `serve.py`: production server entry point
- `utils/`: analysis, forecasts, summaries, and AI integration
- `ml/model.py`: standalone regression helper
- `templates/` and `static/`: dashboard interface
- `tests/`: offline workflow checks

The AI advisor provides decision support. Review its suggestions before acting on them.
