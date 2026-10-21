import datetime as dt
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .store import now
from .cache import Cache, policy

class RateLimited(RuntimeError):
    def __init__(self, message, *, code=None, reset=None, retry_after=None, remaining=None):
        super().__init__(message)
        self.code, self.reset = code, reset
        self.retry_after, self.remaining = retry_after, remaining

class GitHub:
    def __init__(self, store, repo="vllm-project/vllm"):
        self.store, self.repo = store, repo
        self.token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not self.token and shutil.which("gh"):
            p = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            if p.returncode == 0:
                self.token = p.stdout.strip()
        self.raw = store.path.parent / "raw" / "github"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.cache = Cache(store.path.parent)
        self.syncing = False

    def get(self, path, params=None):
        request = {"repo": self.repo, "path": path, "params": params,
                   "auth_scope": hashlib.sha256((self.token or "public").encode()).hexdigest()[:16]}
        result, _ = self.cache.call("github", request, lambda: self._get(path, params), policy()["ttl_seconds"]["github"], self.syncing)
        return result

    def _get(self, path, params=None):
        prefix = "https://api.github.com/repos/" + self.repo + "/"
        url = path if path.startswith("https://api.github.com/") else prefix + path
        parsed = urllib.parse.urlparse(url)
        cursor_params = urllib.parse.parse_qs(parsed.query)
        if "after" in cursor_params or "before" in cursor_params:
            cursor_params.pop("page", None)
            url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(cursor_params, doseq=True)))
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "inference-ideation/0.1"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as res:
                    body = res.read()
                    hdr = dict(res.headers)
                digest = hashlib.sha256(body).hexdigest()
                snapshot = self.raw / (digest + ".json.gz")
                if not snapshot.exists():
                    with gzip.open(snapshot, "wb") as out:
                        out.write(body)
                with (self.raw / "requests.jsonl").open("a") as manifest:
                    manifest.write(json.dumps({"url": url, "fetched_at": now(), "sha256": digest, "snapshot": snapshot.name}) + "\n")
                return json.loads(body), hdr
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    raise RateLimited("GitHub rate/permission response; progress retained.", code=e.code,
                                      reset=e.headers.get("X-RateLimit-Reset"), retry_after=e.headers.get("Retry-After"),
                                      remaining=e.headers.get("X-RateLimit-Remaining")) from e
                if e.code < 500 or attempt == 3:
                    raise
            except (TimeoutError, urllib.error.URLError):
                if attempt == 3:
                    raise
            time.sleep(2 ** attempt)

    def ingest(self, obj, feed="issues"):
        repo = self.repo
        if feed in ("comments", "review_comments"):
            parent_url = obj.get("issue_url") or obj.get("pull_request_url", "")
            number = parent_url.rstrip("/").split("/")[-1]
            id = f"github:{repo}:{feed}:{obj['id']}"
            kind = "review_comment" if feed == "review_comments" else "comment"
            doc = dict(id=id, source="github", kind=kind, title=f"{kind} on {repo} #{number}", body=obj.get("body") or "",
                       url=obj["html_url"], parent=f"github:{repo}:{number}", state=None,
                       created_at=obj.get("created_at"), updated_at=obj.get("updated_at"), metadata={"author": (obj.get("user") or {}).get("login"), "path": obj.get("path"), "commit_id": obj.get("commit_id")})
        else:
            id = f"github:{repo}:{obj['number']}"
            existing = self.store.get(id)
            meta = existing["metadata"] if existing else {}
            is_pr = feed == "pulls" or "pull_request" in obj
            for key in ("number", "labels", "comments", "state_reason"):
                if key in obj:
                    meta[key] = obj[key]
            if feed == "pulls":
                meta.update({k: obj.get(k) for k in ("base", "head", "merge_commit_sha", "draft", "changed_files", "additions", "deletions")})
                # Keep only provenance fields from branch objects; avoid large nested user/repo objects.
                for key in ("base", "head"):
                    meta[key] = {k: (obj.get(key) or {}).get(k) for k in ("ref", "sha", "label")}
                meta["pr_detail_fetched_at"] = now()
            merged = obj.get("merged_at") or (obj.get("pull_request") or {}).get("merged_at") or (existing or {}).get("merged_at")
            doc = dict(id=id, source="github", kind="pr" if is_pr else "issue", title=obj["title"], body=obj.get("body") or "",
                       url=obj["html_url"], created_at=obj.get("created_at"), updated_at=obj.get("updated_at"),
                       state="merged" if merged else obj.get("state"), merged_at=merged, metadata=meta)
        self.store.put(doc)

    def sync(self, feeds=("issues", "pulls", "comments", "review_comments"), max_pages=25, recent_days=None):
        self.syncing = True  # Collector must see current pagination and updates, not a cached feed.
        try:
            return self._sync(feeds, max_pages, recent_days)
        finally:
            self.syncing = False

    def _sync(self, feeds, max_pages, recent_days):
        endpoints = {"issues": "issues", "pulls": "pulls", "comments": "issues/comments", "review_comments": "pulls/comments"}
        for feed in feeds:
            key = self.repo + (":recent:" if recent_days else ":") + feed
            state = self.store.get_checkpoint(key, {})
            if recent_days and not state:
                since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=recent_days)
                state["since"] = since.strftime("%Y-%m-%dT%H:%M:%SZ")
            if not state.get("in_progress"):
                state = {**state, "in_progress": True, "page": 1, "pass_started": now()}
            incremental = bool(state.get("completed_at") or recent_days)
            cutoff = state.get("since")
            page = state["page"]
            if page >= 100 and not state.get("next_url"):
                # Recover checkpoints written by the initial page-based prototype.
                _, previous_headers = self.get(endpoints[feed], {"state": "all", "per_page": 100, "page": page - 1, "sort": "created", "direction": "asc"})
                previous_link = previous_headers.get("Link") or previous_headers.get("link", "")
                match = re.search(r'<([^>]+)>;\s*rel="next"', previous_link)
                if match:
                    state["next_url"] = match.group(1)
            for _ in range(max_pages):
                params = {"state": "all", "per_page": 100, "page": page,
                          "sort": "updated" if incremental else "created", "direction": "desc" if recent_days or (incremental and feed == "pulls") else "asc"}
                if cutoff and feed != "pulls":
                    params["since"] = cutoff
                # Follow GitHub's opaque Link cursor. Page-number pagination is
                # rejected for large issue collections (HTTP 422).
                if state.get("next_url"):
                    items, headers = self.get(state["next_url"])
                else:
                    items, headers = self.get(endpoints[feed], params)
                link = headers.get("Link") or headers.get("link", "")
                next_match = re.search(r'<([^>]+)>;\s*rel="next"', link)
                state["next_url"] = next_match.group(1) if next_match else None
                stop = False
                with self.store.db:
                    for obj in items:
                        if incremental and feed == "pulls" and cutoff and obj["updated_at"] < cutoff:
                            stop = True
                            continue
                        self.ingest(obj, feed)
                    # Commit documents before the cursor, so a crash can only cause a replay.
                page += 1
                state["page"] = page
                state["last_fetch"] = now()
                state["rate_remaining"] = headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining")
                if (not state["next_url"] and len(items) < 100) or stop:
                    start = dt.datetime.fromisoformat(state["pass_started"].replace("Z", "+00:00"))
                    state.update(in_progress=False, completed_at=now(), since=(start - dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), page=1, next_url=None)
                self.store.checkpoint(key, state)
                print(json.dumps({"feed": feed, "page": page - 1, "items": len(items), "complete": not state["in_progress"], "remaining": state["rate_remaining"]}), flush=True)
                if not state["in_progress"]:
                    break
                time.sleep(0.15)

    def hydrate(self, numbers):
        for number in numbers:
            issue, _ = self.get(f"issues/{int(number)}")
            self.ingest(issue)
            feeds = [(f"issues/{number}/comments", "comments")]
            if "pull_request" in issue:
                pr, _ = self.get(f"pulls/{number}")
                self.ingest(pr, "pulls")
                feeds += [(f"pulls/{number}/comments", "review_comments"), (f"pulls/{number}/reviews", "reviews"), (f"pulls/{number}/files", "files")]
            hydration = {}
            for endpoint, kind in feeds:
                page, count = 1, 0
                while True:
                    objs, _ = self.get(endpoint, {"per_page": 100, "page": page})
                    for obj in objs:
                        if kind in ("comments", "review_comments"):
                            self.ingest(obj, kind)
                        else:
                            key = str(obj.get("id") or obj["filename"])
                            self.store.put(dict(id=f"github:{self.repo}:{number}:{kind}:{key}", source="github", kind="diff" if kind == "files" else "review",
                                url=obj.get("html_url") or obj.get("blob_url") or issue["html_url"], title=obj.get("filename") or f"Review #{number} {obj.get('state', '')}",
                                body=obj.get("patch") or obj.get("body") or "", parent=f"github:{self.repo}:{number}",
                                updated_at=obj.get("submitted_at") or issue["updated_at"], metadata={"patch_available": "patch" in obj, "status": obj.get("status"), "review_state": obj.get("state"), "sha": obj.get("sha")}))
                    self.store.db.commit()
                    count += len(objs)
                    if len(objs) < 100:
                        break
                    page += 1
                hydration[kind] = {"count": count, "complete": not (kind == "files" and count >= 3000)}
            self.store.checkpoint(f"hydrated:{self.repo}:{number}", {"at": now(), "collections": hydration})
            print(f"Hydrated {self.repo} #{number}", flush=True)
