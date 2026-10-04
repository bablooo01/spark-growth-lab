# SPARK Growth Lab — Complete Challenge Package

## Start the working full-stack prototype (Windows)
1. Install Python 3.10+.
2. Extract this ZIP fully.
3. Open the `SPARK_FullStack` folder in File Explorer.
4. Open PowerShell in that folder.
5. Run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

6. Open `http://127.0.0.1:8000` for the student-facing experience and growth workspace.
7. Open `http://127.0.0.1:8000/docs` to explore the Python API.
8. Stop the server with Ctrl+C.

If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat` instead.

## What's included
- `SPARK_FullStack/frontend/index.html` — responsive student and growth-workspace UI, styling, animations, transitions, accessible controls, project matchmaker, campaign UTM builder, registration demo, funnel tracker, CSV export, experiment log, seven-day plan.
- `SPARK_FullStack/backend/main.py` — FastAPI routes, input validation, SQLite persistence, duplicate registration handling, observed-only dashboard metrics, and CSV data endpoint.
- `SPARK_FullStack/README.md` — installation, feature overview, routes, limitations, and demo walkthrough.
- `SPARK_FullStack/PROJECT_WALKTHROUGH.md` — frontend/backend/database explanation and presentation guidance.
- `SPARK_FullStack/CHALLENGE_ALIGNMENT.md` — mapping from challenge requirements to project features and honest status.
- `SPARK_Growth_Plan_5_Slides.pptx` — five-slide growth plan.
- `SPARK_AI_Learning_Notes_and_Video_Script.docx` — AI learning notes and three-minute video script.

## Important accuracy notes
- The 500 registrations in seven days and ₹2,000 budget are planning targets for the challenge simulation, not results.
- Seeded funnel data is labelled `demo`. Only records explicitly labelled `observed` are counted as measured campaign outcomes.
- Project recommendations use deterministic rules, not a live LLM/API.
- The registration form stores test submissions locally in SQLite. It does not send email and is not connected to NxtWave systems.
- The application has no authentication and must not be exposed publicly or used for real student data as-is. Use test email addresses only.
- UTM tags label campaign links; they do not independently capture analytics. A real campaign would require an approved destination and an analytics/attribution integration.
- The app is served locally by FastAPI. GitHub Pages alone cannot run the Python backend; public full-stack deployment requires a separate Python-capable host and appropriate security controls.

## Suggested demo order (3 minutes)
1. State the student friction hypothesis: “I don't know what to build.”
2. Use the project matchmaker and explain its transparent rule-based output.
3. Show the demo registration flow using a test email.
4. Open the growth workspace; generate a tagged campaign URL using an approved HTTPS destination only if one is provided.
5. Add a `demo` or `target` funnel record and explain why it is not actual performance.
6. Create an A/B hypothesis; explain that no winner should be declared without comparable exposure and evidence.
7. Show the seven-day plan, ₹2,000 budget guardrails, and API docs.
8. State what remains before production: auth, privacy/security review, approved registration destination, analytics integration, and deployment.
