# SPARK — project walkthrough (challenge demo)

## The two experiences

### 1) Student view — `http://127.0.0.1:8000/`
- Read the workshop concept and try the Project Matchmaker.
- Choose an interest and starting level; the preview is generated with transparent rules (not a live LLM).
- Try the short demo registration form with a test email only.
- The form sends a request to the Python API, which validates it and saves the demo record to SQLite.

### 2) Growth workspace — `http://127.0.0.1:8000/#workspace`
This is for the challenge presenter/campaign owner, not for students.
- **Campaign links:** add the approved HTTPS destination, select channel and creative, then create a tagged link. `utm_source`, `utm_medium`, `utm_campaign`, and `utm_content` are attribution labels; they do not magically measure visits unless the destination analytics captures them.
- **Funnel tracker:** add visits and registrations by day/channel. Use `observed` only for numbers actually measured; use `target` or `demo` for plans and examples.
- **A/B experiment:** record a hypothesis and the two messages before testing. Do not select a winner until comparable exposure and enough data exist.
- **CSV export:** download the event ledger for analysis.
- **Seven-day playbook:** the planned sequence and ₹2,000 budget guardrails from the challenge.

## How the pieces communicate

`Browser UI (HTML/CSS/JavaScript) → HTTP request (/api/...) → FastAPI/Python validation and logic → SQLite database → JSON response → UI updates`

The frontend and API are served from the same local origin. SQLite persists data in `backend/spark.db`, so restarting the server does not normally erase your demo entries.

## Local run

From the `SPARK_FullStack` folder in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000/`. API docs: `http://127.0.0.1:8000/docs`. Health: `http://127.0.0.1:8000/api/health`.

## Important honesty and safety notes

- This is a challenge simulation, not NxtWave's official registration system.
- Use test email addresses only. The demo does not send email or verify identity.
- The internal workspace is separated by the interface only; it has **no login or access control**. Do not expose this app publicly or collect real student data without adding authentication, privacy controls, and a proper production database.
- The project matcher is rule-based, not a live AI API.
- The funnel targets (500 registrations / 7 days / ₹2,000) are planning goals. Do not describe them as achieved results.
- The campaign-link builder requires an approved HTTPS registration destination. `example.com` or a placeholder is not a real registration destination.
