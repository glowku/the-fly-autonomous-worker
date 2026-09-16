"""Client GitHub minimal avec gestion des rate limits."""
import os, time, base64, requests

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def gh(method, path, retries=5, **kwargs):
    """Requête GitHub avec backoff exponentiel."""
    url = path if path.startswith("http") else f"{API}{path}"
    headers = {**HEADERS, **kwargs.pop("headers", {})}
    for attempt in range(retries):
        r = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        if r.status_code in (403, 429):
            wait = int(r.headers.get("Retry-After", 2 ** attempt * 5))
            time.sleep(min(wait, 60))
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json() if r.content else {}
    raise RuntimeError(f"Échec {method} {url} après {retries} essais")

def create_or_update_file(repo, path, content, message, branch="main"):
    """Commit un fichier via l'API Contents (pas de clone)."""
    sha = None
    try:
        existing = gh("GET", f"/repos/{repo}/contents/{path}?ref={branch}")
        sha = existing.get("sha")
    except requests.HTTPError:
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