from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "nexus.db"
REPORTS = ROOT / "reports"

def now():
    return datetime.now(timezone.utc).isoformat()

def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()

def fingerprint(text):
    return hashlib.sha256(normalize(text).encode()).hexdigest()[:16]

def db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS patterns(
        fingerprint TEXT PRIMARY KEY,
        problem TEXT NOT NULL,
        status TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        pass_count INTEGER NOT NULL DEFAULT 0,
        fail_count INTEGER NOT NULL DEFAULT 0,
        root_cause TEXT,
        solution TEXT,
        updated_at TEXT NOT NULL
    )
    """)
    conn.commit()
    return conn

def remember(problem, status, root_cause="", solution=""):
    status = status.upper()

    if status not in {"PASS","FAIL","BLOCKED","UNKNOWN"}:
        raise ValueError("Ongeldige status")

    fp = fingerprint(problem)

    with db() as conn:
        row = conn.execute(
            "SELECT attempts,pass_count,fail_count FROM patterns WHERE fingerprint=?",
            (fp,)
        ).fetchone()

        attempts, pc, fc = row if row else (0,0,0)

        attempts += 1
        pc += int(status == "PASS")
        fc += int(status == "FAIL")

        conn.execute("""
        INSERT INTO patterns(
            fingerprint,problem,status,attempts,pass_count,fail_count,
            root_cause,solution,updated_at
        )
        VALUES(?,?,?,?,?,?,?,?,?)
        ON CONFLICT(fingerprint) DO UPDATE SET
            problem=excluded.problem,
            status=excluded.status,
            attempts=excluded.attempts,
            pass_count=excluded.pass_count,
            fail_count=excluded.fail_count,
            root_cause=CASE
                WHEN excluded.root_cause!='' THEN excluded.root_cause
                ELSE patterns.root_cause
            END,
            solution=CASE
                WHEN excluded.solution!='' THEN excluded.solution
                ELSE patterns.solution
            END,
            updated_at=excluded.updated_at
        """,(
            fp,problem,status,attempts,pc,fc,
            root_cause,solution,now()
        ))

        conn.commit()

    return analyze(problem)

def analyze(problem):
    fp = fingerprint(problem)

    with db() as conn:
        row = conn.execute("""
        SELECT fingerprint,problem,status,attempts,
               pass_count,fail_count,root_cause,solution,updated_at
        FROM patterns
        WHERE fingerprint=?
        """,(fp,)).fetchone()

    if not row:
        return {
            "fingerprint": fp,
            "known": False,
            "recommendation": "NEW_PATTERN"
        }

    keys = [
        "fingerprint","problem","status","attempts",
        "pass_count","fail_count","root_cause",
        "solution","updated_at"
    ]

    result = dict(zip(keys,row))
    result["known"] = True

    if result["fail_count"] >= 3 and result["pass_count"] == 0:
        result["recommendation"] = "STOP_REPEAT_AND_CHANGE_STRATEGY"
    elif result["pass_count"] > 0:
        result["recommendation"] = "KNOWN_GOOD_PATTERN"
    else:
        result["recommendation"] = "CONTINUE_WITH_EVIDENCE"

    return result

def run(cmd, timeout=45):
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "cmd": cmd,
            "returncode": p.returncode,
            "stdout": p.stdout[-5000:],
            "stderr": p.stderr[-5000:]
        }
    except subprocess.TimeoutExpired:
        return {
            "cmd": cmd,
            "returncode": 124,
            "stdout": "",
            "stderr": "TIMEOUT"
        }

def security_scan():
    """
    Detect probable credentials rather than bare prefixes.

    This avoids the scanner detecting its own source while keeping
    realistic credential detection active.
    """

    secret_patterns = (
        re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),
        re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
        re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
    )

    ignored_dirs = {
        ".git",
        "logs",
        "data",
        "__pycache__",
        ".venv",
        "venv",
    }

    hits = []

    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue

        if any(part in ignored_dirs for part in p.parts):
            continue

        try:
            content = p.read_text(errors="ignore")
        except Exception:
            continue

        if any(pattern.search(content) for pattern in secret_patterns):
            hits.append(str(p.relative_to(ROOT)))

    return sorted(set(hits))

def performance_check():
    return {
        "python_files": len(list(ROOT.rglob("*.py"))),
        "shell_files": len(list(ROOT.rglob("*.sh"))) + len(list((ROOT/"bin").glob("*"))),
        "database_exists": DB.exists()
    }

def architecture(idea):
    slug = "-".join(
        "".join(
            c.lower() if c.isalnum() else " "
            for c in idea
        ).split()
    )[:48] or "new-project"

    return {
        "name": slug,
        "goal": idea,
        "architecture": [
            "cli",
            "core",
            "repair-memory",
            "security",
            "tests",
            "github-ci"
        ],
        "workflow": [
            "UNDERSTAND",
            "INSPECT",
            "DEDUPLICATE",
            "ARCHITECT",
            "PLAN",
            "BUILD",
            "TEST",
            "DEBUG",
            "REPAIR",
            "SECURITY",
            "PERFORMANCE",
            "REGRESSION",
            "VERIFY",
            "LEARN"
        ],
        "gates": [
            "BUILD_PASS",
            "TEST_PASS",
            "SECURITY_PASS",
            "REGRESSION_PASS"
        ]
    }

def safe_repair():
    actions = []

    for p in [ROOT/"data",ROOT/"logs",ROOT/"reports"]:
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            actions.append(f"created {p.relative_to(ROOT)}")

    for p in [
        ROOT/"nexus.py",
        ROOT/"bin/nexus",
        ROOT/"bin/repair-bot",
        ROOT/"tests/test.sh"
    ]:
        if p.exists() and not os.access(p, os.X_OK):
            p.chmod(p.stat().st_mode | 0o111)
            actions.append(f"chmod +x {p.relative_to(ROOT)}")

    with db():
        pass

    actions.append("verified sqlite schema")

    return actions

def full_test():
    commands = [
        ["python","-m","py_compile","nexus.py","nexuslib/core.py"],
        ["bash","-n","bin/nexus"],
        ["bash","-n","bin/repair-bot"],
        ["bash","-n","tests/test.sh"],
        ["python","nexus.py","selftest"]
    ]

    results = [run(cmd) for cmd in commands]

    passed = all(r["returncode"] == 0 for r in results)

    REPORTS.mkdir(exist_ok=True)

    (REPORTS/"last-test.json").write_text(
        json.dumps({
            "ok": passed,
            "results": results
        },indent=2)
    )

    return passed, results
