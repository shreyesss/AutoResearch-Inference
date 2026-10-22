import hashlib
import datetime as dt
import base64
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from .store import now
from .cache import Cache, policy

def arxiv_query(query, relaxed=False):
    if re.search(r"\b(?:all|ti|au|abs|cat|id):", query):
        return query
    stop = {"a", "an", "the", "of", "for", "and", "or", "in", "on", "under", "with", "to", "per", "based"}
    terms = [phrase or word for phrase, word in re.findall(r'"([^"]+)"|(\S+)', query)]
    terms = [t for t in terms if t.lower() not in stop]
    terms = terms[:3] if relaxed else terms[:10]
    return " AND ".join('all:"' + t.replace('"', '') + '"' for t in terms)

class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "noscript"):
            self.skip += 1
        if tag in ("p", "div", "h1", "h2", "h3", "li", "br"):
            self.parts.append("\n")
        if tag == "a" and not self.skip:
            href = dict(attrs).get("href", "")
            if href.startswith("https://"):
                self.parts.append(" " + href + " ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

class Sources:
    def __init__(self, store):
        self.store = store
        self.cache = Cache(store.path.parent)
        self.refresh = False

    def request(self, url, xml=False, headers=None):
        ttl = policy()["ttl_seconds"]
        immutable = bool(re.search(r"raw.githubusercontent.com/[^/]+/[^/]+/[0-9a-fA-F]{40}/|arxiv.org/(?:html|pdf)/\d{4}\.\d+v\d+", url))
        lifetime = ttl["immutable"] if immutable else ttl["search"] if "/api/" in url or "/api?" in url else ttl["page"]
        def fetch():
            try:
                raw, content_type = self._request(url, xml, headers)
                return {"data": base64.b64encode(raw).decode(), "content_type": content_type}
            except urllib.error.HTTPError as error:
                if error.code in (404, 410):
                    return {"http_error": error.code}
                raise
        result, self.last_cache = self.cache.call("source_http", {"url": url, "xml": xml}, fetch, lifetime, self.refresh)
        if "http_error" in result:
            raise urllib.error.HTTPError(url, result["http_error"], "Cached missing source", {}, None)
        return base64.b64decode(result["data"]), result["content_type"]

    def _request(self, url, xml=False, headers=None):
        if urllib.parse.urlparse(url).hostname in ("export.arxiv.org", "arxiv.org"):
            last = self.store.get_checkpoint("arxiv:last_request", 0)
            time.sleep(max(0, 3.1 - (time.time() - last)))
            self.store.checkpoint("arxiv:last_request", time.time())
        req = urllib.request.Request(url, headers={"User-Agent": "inference-ideation/0.1 (research prototype)", "Accept": "application/atom+xml" if xml else "*/*", **(headers or {})})
        with urllib.request.urlopen(req, timeout=40) as res:
            data = res.read(8_000_001)
            if len(data) > 8_000_000:
                raise ValueError("Source exceeds 8 MB; fetch a focused section instead")
            ctype = res.headers.get("Content-Type", "")
        raw = self.store.path.parent / "raw" / "sources"
        raw.mkdir(parents=True, exist_ok=True)
        (raw / hashlib.sha256(data).hexdigest()).write_bytes(data)
        return data, ctype

    def papers(self, query, limit=8, provider="both", after=None, before=None):
        results, errors, attempts = [], [], []
        if provider in ("arxiv", "both"):
            try:
                ns = {"a": "http://www.w3.org/2005/Atom"}
                effective = arxiv_query(query)
                entries = []
                # Relax the user's words BEFORE adding field/date syntax. Never
                # drop dates or rewrite explicit Boolean queries on a retry.
                variants = list(dict.fromkeys(arxiv_query(query, relaxed=r) for r in (False, True)))
                for index, variant in enumerate(variants):
                    effective = variant
                    if after or before:
                        first = (after or '1991-01-01').replace('-', '') + '0000'
                        end = dt.date.fromisoformat(before) - dt.timedelta(days=1) if before else dt.date(2099, 12, 31)
                        effective = '(' + variant + ') AND submittedDate:[' + first + ' TO ' + end.strftime('%Y%m%d') + '2359]'
                    params = urllib.parse.urlencode({"search_query": effective, "start": 0, "max_results": limit, "sortBy": "relevance"})
                    raw, _ = self.request("https://export.arxiv.org/api/query?" + params, xml=True)
                    entries = ET.fromstring(raw).findall("a:entry", ns)
                    attempts.append({'query': effective, 'relaxed': index > 0, 'returned': len(entries),
                                     'cache': getattr(self, 'last_cache', None)})
                    if entries:
                        break
                for e in entries:
                    url = e.findtext("a:id", "", ns).replace("http://", "https://")
                    arxiv_id = re.sub(r"v\d+$", "", url.rsplit("/", 1)[-1])
                    doc = dict(id="arxiv:" + arxiv_id, source="arxiv", kind="paper", url=url, title=" ".join(e.findtext("a:title", "", ns).split()), body=e.findtext("a:summary", "", ns), created_at=e.findtext("a:published", None, ns), updated_at=e.findtext("a:updated", None, ns), metadata={"read_depth": "abstract", "authors": [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)], "query": query, "effective_arxiv_query": effective})
                    self.store.put(doc)
                    results.append(doc["id"])
            except Exception as e:
                errors.append({"provider": "arxiv", "error_type": type(e).__name__})
        if provider in ("hf", "both"):
            try:
                raw, _ = self.request("https://huggingface.co/api/papers/search?" + urllib.parse.urlencode({"q": query, "limit": limit}))
                for entry in json.loads(raw)[:limit]:
                    e = entry.get("paper", entry)
                    arxiv_id = e["id"]
                    # Separate source documents, joined by canonical paper identity.
                    doc = dict(id="hf:" + arxiv_id, source="huggingface", kind="paper", url="https://huggingface.co/papers/" + arxiv_id, title=e.get("title", ""), body=e.get("summary", ""), created_at=e.get("publishedAt"), updated_at=e.get("publishedAt"), metadata={"read_depth": "abstract", "query": query, "githubRepo": e.get("githubRepo"), "arxiv_id": arxiv_id})
                    self.store.put(doc)
                    self.store.edge(doc["id"], "same_paper", "arxiv:" + arxiv_id, doc["id"], {"basis": "arxiv id"})
                    if e.get("githubRepo"):
                        self.store.edge(doc["id"], "implementation", e["githubRepo"], doc["id"], {})
                    results.append(doc["id"])
            except Exception as e:
                errors.append({"provider": "hf", "error": str(e)})
        self.store.db.commit()
        return {"query": query, "ids": results, "errors": errors, 'attempts': attempts}

    def fetch(self, url, refresh=False):
        self.refresh = refresh
        parsed = urllib.parse.urlparse(url)
        allowed = {"arxiv.org", "export.arxiv.org", "huggingface.co", "raw.githubusercontent.com", "docs.vllm.ai", "autoloops.ai"}
        if parsed.scheme != "https" or parsed.hostname not in allowed:
            raise ValueError("Fetch supports HTTPS primary sources only: " + ", ".join(sorted(allowed)))
        arxiv = re.search(r"arxiv.org/(?:abs|html|pdf)/(\d{4}\.\d+)(v\d+)?", url)
        requested = arxiv.group(1) + (arxiv.group(2) or "") if arxiv else None
        if arxiv and not parsed.path.startswith("/pdf/"):
            url = "https://arxiv.org/html/" + requested
        try:
            raw, ctype = self.request(url)
        except urllib.error.HTTPError as e:
            if not arxiv or e.code != 404:
                raise
            url = "https://arxiv.org/pdf/" + requested
            raw, ctype = self.request(url)
        parser_name = "plain_text"
        if "pdf" in ctype:
            try:
                from pypdf import PdfReader
            except ImportError as e:
                raise ValueError("PDF requires pypdf; install requirements-research.txt") from e
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join(f"[PDF page {i+1}]\n" + (page.extract_text() or "") for i, page in enumerate(reader.pages))
            if len(text.strip()) < 200:
                raise ValueError("PDF text extraction insufficient; OCR/visual inspection required")
            parser_name = "pypdf; text only, no OCR or figure interpretation"
        else:
            text = raw.decode("utf-8", errors="replace")
        if "html" in ctype:
            parser = TextHTML()
            parser.feed(text)
            text = re.sub(r"[ \t]+", " ", "".join(parser.parts))
            parser_name = "html_text"
        id = "fulltext:" + requested if arxiv else "web:" + hashlib.sha256(url.encode()).hexdigest()[:16]
        self.store.put(dict(id=id, source=parsed.hostname, kind="fulltext" if arxiv else "resource", url=url, title=url, body=text, parent="arxiv:" + arxiv.group(1) if arxiv else None, metadata={"read_depth": "fulltext_available", "characters": len(text), "parser": parser_name, "sha256": hashlib.sha256(raw).hexdigest(), "retrieval_cache": self.last_cache}))
        self.store.db.commit()
        return {"id": id, "url": url, "characters": len(text), "cache": self.last_cache}

    def expand(self, id, limit=5):
        """Follow explicit arXiv links; inferred relations never become citations."""
        doc = self.store.get(id)
        if not doc:
            raise ValueError("Unknown source " + id)
        ids = list(dict.fromkeys(re.findall(r"arxiv.org/(?:abs|html|pdf)/(\d{4}\.\d+)", doc["body"])))[:limit]
        results = []
        for paper in ids:
            try:
                result = self.fetch("https://arxiv.org/abs/" + paper)
                self.store.edge(id, "references", result["id"], id, {"basis": "explicit hyperlink; relevance not assumed"})
                results.append(result)
            except Exception as e:
                results.append({"paper": paper, "error": str(e)})
        self.store.db.commit()
        return results

    def code(self, repo, ref, path):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("Expected owner/repository")
        if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
            raise ValueError("Use an exact 40-character commit SHA for reproducible source inspection")
        if path.startswith("/") or ".." in path.split("/"):
            raise ValueError("Expected a repository-relative file path")
        url = f"https://raw.githubusercontent.com/{repo}/{ref}/" + urllib.parse.quote(path, safe="/")
        raw, _ = self.request(url)
        id = f"code:{repo}:{ref}:{path}"
        self.store.put(dict(id=id, source="github-code", kind="code", url=url, title=path, body=raw.decode("utf-8"), metadata={"repo": repo, "commit": ref, "path": path, "sha256": hashlib.sha256(raw).hexdigest(), "read_depth": "full_file_available"}))
        self.store.db.commit()
        return {"id": id, "characters": len(raw)}

    def citations(self, id, limit=5):
        paper = id.split(":", 1)[-1]
        if not re.fullmatch(r"\d{4}\.\d+", paper):
            raise ValueError("Use arxiv:YYMM.NNNNN")
        fields = "title,url,references.title,references.externalIds,references.url,citations.title,citations.externalIds,citations.url"
        url = "https://api.semanticscholar.org/graph/v1/paper/ARXIV:" + paper + "?" + urllib.parse.urlencode({"fields": fields})
        headers = {"User-Agent": "inference-ideation/0.1"}
        if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
            headers["x-api-key"] = os.environ["SEMANTIC_SCHOLAR_API_KEY"]
        try:
            raw, _ = self.request(url, headers=headers)
            data = json.loads(raw)
        except urllib.error.HTTPError as e:
            return {"error": f"Semantic Scholar HTTP {e.code}; public rate limits apply. Optional SEMANTIC_SCHOLAR_API_KEY enables authenticated use.", "ids": []}
        results = []
        for relation in ("references", "citations"):
            for entry in data.get(relation, [])[:limit]:
                external = (entry.get("externalIds") or {}).get("ArXiv")
                dst = "arxiv:" + external if external else entry.get("url")
                if dst:
                    src, target = ("arxiv:" + paper, dst) if relation == "references" else (dst, "arxiv:" + paper)
                    self.store.edge(src, "cites", target, url, {"title": entry.get("title"), "provider": "Semantic Scholar", "fetched_at": now(), "meaning": "bibliographic relation; no support/endorsement inferred"})
                    results.append(dst)
        self.store.db.commit()
        return {"id": id, "ids": results, "provider": url}
