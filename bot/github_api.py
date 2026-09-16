"""Client GitHub avec gestion du secondary rate limit."""
import os
import time
import base64
import requests

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# GitHub secondary rate limit : minimum 1s entre 2 écritures
_last_write = 0.0
_MIN_WRITE_INTERVAL = 1.2  # marge de sécurité


def _throttle_writes():
    """Espace les écritures pour éviter le secondary rate limit."""
    global _last_write
    now = time.time()
    delta = now - _last_write
    if delta < _MIN_WRITE_INTERVAL:
        time.sleep(_MIN_WRITE_INTERVAL - delta)
    _last_write = time.time()


def gh(method, path, retries=5, **kwargs):
    """Requête GitHub avec throttle sur les écritures + backoff."""
    url = path if path.startswith("http") else f"{API}{path}"
    headers = {**HEADERS, **kwargs.pop("headers", {})}
    is_write = method in ("POST", "PUT", "PATCH", "DELETE")

    for attempt in range(retries):
        if is_write:
            _throttle_writes()

        try:
            r = requests.request(method, url, headers=headers, timeout=15, **kwargs)
        except requests.RequestException as e:
            print(f"  [gh] réseau {method} {url} → {e}", flush=True)
            time.sleep(2)
            continue

        if r.status_code in (403, 429):
            retry_after = int(r.headers.get("Retry-After", 0))
            body = r.text[:200]
            # 403 "Resource not accessible" = problème de permissions, on abandonne
            if r.status_code == 403 and "Resource not accessible" in body:
                print(f"  [gh] 403 permissions sur {method} {url}", flush=True)
                print(f"  [gh] corps: {body}", flush=True)
                raise PermissionError(f"PAT_TOKEN sans les droits suffisants sur {url}")

            # Sinon c'est du throttling : on attend et on retry
            wait = max(retry_after, 2 ** attempt, 5)
            print(
                f"  [gh] {r.status_code} throttle sur {method} {url} "
                f"(attente {wait}s, tentative {attempt+1}/{retries})",
                flush=True,
            )
            time.sleep(wait)
            continue

        if r.status_code >= 500:
            print(f"  [gh] {r.status_code} serveur, retry {attempt+1}", flush=True)
            time.sleep(2 ** attempt)
            continue

        if r.status_code >= 400:
            print(f"  [gh] {r.status_code} sur {method} {url}", flush=True)
            print(f"  [gh] corps: {r.text[:300]}", flush=True)

        r.raise_for_status()
        return r.json() if r.content else {}

    raise RuntimeError(f"Échec {method} {url} après {retries} essais")


def create_file(repo, path, content, message, branch="main"):
    """Crée un NOUVEAU fichier — pas de GET préalable, 1 seul appel API."""
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
    }
    return gh("PUT", f"/repos/{repo}/contents/{path}", json=payload)


def create_or_update_file(repo, path, content, message, branch="main"):
    """Crée ou met à jour un fichier — fait un GET pour récupérer le sha."""
    sha = None
    try:
        existing = gh("GET", f"/repos/{repo}/contents/{path}?ref={branch}")
        sha = existing.get("sha")
    except Exception:
        pass

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    return gh("PUT", f"/repos/{repo}/contents/{path}", json=payload)


def get_default_branch(repo):
    return gh("GET", f"/repos/{repo}").get("default_branch", "main")