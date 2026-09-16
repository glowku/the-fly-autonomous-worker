"""Gestion de l'état partagé, stocké dans state.json du repo."""
import json
import base64
import os
from datetime import datetime, timezone

from .github_api import gh, create_or_update_file

STATE_FILE = "state.json"
REPO = os.environ.get("TARGET_REPO", "glowku/the-fly-autonomous-worker")


def default():
    return {
        "total_commits": 0,
        "total_prs": 0,
        "total_reviews": 0,
        "total_issues": 0,
        "last_run": None,
        "hawkes_seed": 42,
    }


def load():
    """Charge l'état depuis le repo. Retourne le défaut si absent."""
    try:
        data = gh("GET", f"/repos/{REPO}/contents/{STATE_FILE}")
        content = base64.b64decode(data["content"]).decode()
        state = json.loads(content)
        # Garantit que tous les champs existent même sur un vieux state.json
        merged = default()
        merged.update(state)
        return merged
    except Exception:
        return default()


def save(state):
    """Écrit l'état dans le repo."""
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    create_or_update_file(
        REPO,
        STATE_FILE,
        json.dumps(state, indent=2) + "\n",
        "chore(state): update bot state [skip ci]",
    )
    return state


def bump(key, n=1):
    s = load()
    s[key] = s.get(key, 0) + n
    return save(s)