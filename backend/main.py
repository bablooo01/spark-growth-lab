from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import re
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(__file__).resolve().parent / "spark.db"
FRONTEND_PATH = ROOT / "frontend"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            channel TEXT NOT NULL,
            visits INTEGER NOT NULL CHECK(visits >= 0),
            registrations INTEGER NOT NULL CHECK(registrations >= 0),
            record_type TEXT NOT NULL CHECK(record_type IN ('demo','target','observed')),
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hypothesis TEXT NOT NULL,
            variant_a TEXT NOT NULL,
            variant_b TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planned' CHECK(status IN ('planned','running','completed')),
            winner TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            interest TEXT NOT NULL,
            skill_level TEXT NOT NULL,
            consent INTEGER NOT NULL DEFAULT 1,
            source TEXT NOT NULL DEFAULT 'direct',
            created_at TEXT NOT NULL,
            UNIQUE(email)
        );
        """)
        # A clearly labelled demo record makes the dashboard immediately explorable.
        count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        if count == 0:
            con.execute(
                """INSERT INTO events(day,channel,visits,registrations,record_type,note,created_at)
                VALUES(?,?,?,?,?,?,?)""",
                ("Day 1", "Demo / sample", 100, 10, "demo",
                 "Illustrative sample only; not campaign results.", now_iso())
            )

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

class EventIn(BaseModel):
    day: str = Field(min_length=1, max_length=30)
    channel: str = Field(min_length=1, max_length=80)
    visits: int = Field(ge=0, le=10_000_000)
    registrations: int = Field(ge=0, le=10_000_000)
    record_type: str = Field(pattern="^(demo|target|observed)$")
    note: str = Field(default="", max_length=1000)

class ExperimentIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    hypothesis: str = Field(min_length=5, max_length=1000)
    variant_a: str = Field(min_length=1, max_length=500)
    variant_b: str = Field(min_length=1, max_length=500)
    status: str = Field(default="planned", pattern="^(planned|running|completed)$")
    winner: str = Field(default="", max_length=20)
    notes: str = Field(default="", max_length=1000)

class RegistrationIn(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    interest: str = Field(min_length=2, max_length=80)
    skill_level: str = Field(min_length=2, max_length=80)
    consent: bool = True
    source: str = Field(default="direct", max_length=120)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="SPARK Growth Lab API",
    description="Backend API for the SPARK student-first growth experiment prototype.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your deployed frontend domain for production.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SPARK Growth Lab API", "time": now_iso()}

@app.get("/api/dashboard")
def dashboard():
    with connect() as con:
        rows = con.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
        reg_count = con.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
        experiments = con.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
    events = [dict(r) for r in rows]
    # Only observed records should be described as real observed campaign data.
    observed_visits = sum(r["visits"] for r in events if r["record_type"] == "observed")
    observed_regs = sum(r["registrations"] for r in events if r["record_type"] == "observed")
    return {
        "events": events,
        "totals": {
            "event_records": len(events),
            "observed_visits": observed_visits,
            "observed_registrations": observed_regs,
            "observed_conversion_pct": round(observed_regs / observed_visits * 100, 2) if observed_visits else 0,
            "registrations_submitted_to_demo_form": reg_count,
            "experiments": experiments,
        },
        "notice": "Demo and target records are illustrative; only records labelled observed represent measured campaign data."
    }

@app.post("/api/events", status_code=201)
def create_event(payload: EventIn):
    if payload.registrations > payload.visits:
        raise HTTPException(status_code=422, detail="Registrations cannot exceed visits in this simple funnel record.")
    with connect() as con:
        cur = con.execute(
            """INSERT INTO events(day,channel,visits,registrations,record_type,note,created_at)
            VALUES(?,?,?,?,?,?,?)""",
            (payload.day, payload.channel, payload.visits, payload.registrations,
             payload.record_type, payload.note, now_iso())
        )
        row = con.execute("SELECT * FROM events WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int):
    with connect() as con:
        cur = con.execute("DELETE FROM events WHERE id=?", (event_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Event record not found.")
    return {"deleted": event_id}

@app.get("/api/events/export")
def export_events():
    with connect() as con:
        rows = con.execute("SELECT id,day,channel,visits,registrations,record_type,note,created_at FROM events ORDER BY id").fetchall()
    return {"columns": ["id","day","channel","visits","registrations","record_type","note","created_at"],
            "rows": [dict(r) for r in rows]}

@app.get("/api/experiments")
def list_experiments():
    with connect() as con:
        rows = con.execute("SELECT * FROM experiments ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/api/experiments", status_code=201)
def create_experiment(payload: ExperimentIn):
    with connect() as con:
        cur = con.execute(
            """INSERT INTO experiments(name,hypothesis,variant_a,variant_b,status,winner,notes,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (payload.name, payload.hypothesis, payload.variant_a, payload.variant_b,
             payload.status, payload.winner, payload.notes, now_iso())
        )
        row = con.execute("SELECT * FROM experiments WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)

@app.patch("/api/experiments/{experiment_id}")
def update_experiment(experiment_id: int, payload: ExperimentIn):
    with connect() as con:
        cur = con.execute(
            """UPDATE experiments SET name=?,hypothesis=?,variant_a=?,variant_b=?,status=?,winner=?,notes=?
            WHERE id=?""",
            (payload.name, payload.hypothesis, payload.variant_a, payload.variant_b,
             payload.status, payload.winner, payload.notes, experiment_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Experiment not found.")
        row = con.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
    return dict(row)

@app.delete("/api/experiments/{experiment_id}")
def delete_experiment(experiment_id: int):
    with connect() as con:
        cur = con.execute("DELETE FROM experiments WHERE id=?", (experiment_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Experiment not found.")
    return {"deleted": experiment_id}

@app.post("/api/registrations", status_code=201)
def register(payload: RegistrationIn, source: Optional[str] = Query(default=None, max_length=120)):
    email = payload.email.strip().lower()
    # Basic practical email syntax check: one @, non-empty local/domain parts,
    # no whitespace, and a dotted domain with non-empty labels.
    email_pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
    if not re.fullmatch(email_pattern, email) or len(email) > 254 or '..' in email.split('@', 1)[0]:
        raise HTTPException(status_code=422, detail="Enter a valid email address, such as student@example.com.")
    if not payload.consent:
        raise HTTPException(status_code=422, detail="Consent is required for this demo registration.")
    with connect() as con:
        try:
            cur = con.execute(
                """INSERT INTO registrations(email,interest,skill_level,consent,source,created_at)
                VALUES(?,?,?,?,?,?)""",
                (email, payload.interest, payload.skill_level, int(payload.consent),
                 (source or payload.source or "direct")[:120], now_iso())
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="This email has already registered in this demo.")
        return {"id": cur.lastrowid, "message": "Demo registration saved successfully.",
                "source": source or payload.source or "direct"}

@app.get("/api/registrations/count")
def registration_count():
    with connect() as con:
        count = con.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    return {"count": count, "note": "This is the count of demo form submissions stored in the local SQLite database."}

# Serve the frontend from the same FastAPI process, so the project works from one local URL.
app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
