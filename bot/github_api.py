"""Client GitHub minimal avec gestion des rate limits."""
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


def gh(method, path, retries=3, **kwargs):
    """Requête GitHub avec logs immédiats sur erreur."""
    url = path if path.startswith("http") else f"{API}{path}"
    headers = {**HEADERS, **kwargs.pop("headers", {})}

    for attempt in range(retries):
        try:
            r = requests.request(method, url, headers=headers, timeout=10, **kwargs)
        except requests.RequestException as e:
            print(f"  [gh] réseau {method} {url} → {e}", flush=True)
            time.sleep(2)
            continue

        if r.status_code in (403, 429):
            retry_after = int(r.headers.get("Retry-After", 5))
            print(
                f"  [gh] {r.status_code} sur {method} {url} "
                f"(retry-after={retry_after}s, tentative {attempt+1}/{retries})",
                flush=True,
            )
            # 403 sans retry-after = problème de permission, pas de rate limit
            if retry_after <= 1:
                print(f"  [gh] corps: {r.text[:300]}", flush=True)
                raise PermissionError(
                    f"403 sur {url}. Vérifie les permissions du PAT_TOKEN."
                )
            time.sleep(min(retry_after, 10))
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


def create_or_update_file(repo, path, content, message, branch="main"):
    """Commit un fichier via l'API Contents (pas de clone)."""
    sha = None
    try:
        existing = gh("GET", f"/repos/{repo}/contents/{path}?ref={branch}")
        sha = existing.get("sha")
    except requests.HTTPError:
        pass
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