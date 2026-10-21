"""Bounded primary-source reading before optional evidence/hypothesis reasoning."""
import contextlib
import hashlib
import json
import re
import sys
from pathlib import Path

from .evidence import ResearchTools, canonical, new_output, write_json
from .github import GitHub
from .sources import Sources
from .store import now


def _arxiv_target(doc, store):
    """Use the selected revision when known; never invent a v1 pin."""
    identity = canonical(doc)
    paper = identity.split(":", 1)[1]
    candidates = [doc]
    counterpart = store.get(identity)
    if counterpart and counterpart["id"] != doc["id"]:
        candidates.append(counterpart)
    for candidate in candidates:
        values = [candidate.get("metadata", {}).get("arxiv_version", ""), candidate.get("url", ""), candidate["id"]]
        for value in values:
            match = re.search(re.escape(paper) + r"v\d+(?!\d)", value)
            if match:
                return match.group(), candidate
    return paper, doc


def _repository_links(doc):
    """Rank by explicit source location, never by a repository's name."""
    candidates = []
    metadata_repo = doc.get("metadata", {}).get("githubRepo")
    if isinstance(metadata_repo, str):
        names = re.findall(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", metadata_repo)
        if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", metadata_repo):
            names.append(metadata_repo)
        candidates += [(name, "explicit githubRepo metadata") for name in names]
    body_basis = "fulltext link; may be a cited dependency" if doc.get("kind") == "fulltext" else "original selected source link"
    candidates += [(name, body_basis) for name in re.findall(
        r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", doc.get("body", ""))]
    seen, result = set(), []
    for name, basis in candidates:
        repo = name.rstrip(".,;").removesuffix(".git")
        if repo not in seen:
            seen.add(repo)
            result.append({"repository": repo, "basis": basis, "link_source_id": doc["id"]})
    return result


def _round_robin_repositories(groups, limit):
    """Give each selected source a candidate before spending slots on extras."""
    queues = [list(group) for group in groups]
    result, seen = [], set()
    while len(result) < limit:
        advanced = False
        for queue in queues:
            while queue and queue[0]["repository"] in seen:
                queue.pop(0)
            if queue:
                choice = queue.pop(0)
                result.append(choice)
                seen.add(choice["repository"])
                advanced = True
                if len(result) >= limit:
                    break
        if not advanced:
            break
    return result


def investigate(store, question, source_ids, output, *, max_http_calls=12,
                max_fulltexts=3, max_repositories=2, citations_per_paper=3,
                code_sources=None, max_code_files=6,
                reason=False, brief=None, model=None, timeout=300):
    """Fetch original text/code under a shared cache-miss budget; never run GPUs.

    A source dossier is not a verified scientific conclusion. Optional reasoning
    uses the existing quote validator and task-derived hypothesis rubric.
    """
    if not question.strip() or not source_ids:
        raise ValueError("Provide a question and at least one stored source ID")
    if len(source_ids) > 20 or any(int(n) < 0 for n in (max_http_calls, max_fulltexts, max_repositories, citations_per_paper, max_code_files)):
        raise ValueError("At most 20 sources; budgets must be nonnegative")
    if reason and not brief:
        raise ValueError("Reasoning requires an explicit task brief with baseline and objective")
    brief_data = brief if isinstance(brief, dict) else json.loads(Path(brief).read_text()) if brief else {}
    if not isinstance(brief_data, dict):
        raise ValueError("Task brief must be a JSON object")
    pinned_requests = {}
    for requested_by, entries in (("argument", [] if code_sources is None else code_sources), ("brief", brief_data.get("code_sources", []))):
        if not isinstance(entries, list):
            raise ValueError("code_sources must be a list of {repo, ref, path}")
        for entry in entries:
            if not isinstance(entry, dict) or any(not isinstance(entry.get(field), str) for field in ("repo", "ref", "path")):
                raise ValueError("Every code source needs string repo, ref and path")
            repo, ref, path = entry["repo"], entry["ref"], entry["path"]
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
                raise ValueError("Code source requires owner/repository and an exact 40-hex commit")
            if not path or path.startswith("/") or ".." in path.split("/") or "\\" in path or any(ord(c) < 32 for c in path):
                raise ValueError("Code source requires a safe repository-relative file path")
            key = (repo, ref.lower(), path)
            pinned_requests.setdefault(key, []).append(requested_by)
    if len(pinned_requests) > max_code_files:
        raise ValueError("Requested pinned code files exceed max_code_files; narrow selection or explicitly raise the limit")
    selected = [store.get(identity) for identity in dict.fromkeys(source_ids)]
    if any(doc is None for doc in selected):
        raise ValueError("Selected source is not in the corpus")
    out = new_output(output)
    brief_for_reasoning = brief
    if reason and isinstance(brief, dict):
        write_json(out / "brief.json", brief_data)
        brief_for_reasoning = str(out / "brief.json")
    used = 0

    def spend():
        nonlocal used
        if used >= max_http_calls:
            raise RuntimeError("Deep-read HTTP budget exhausted")
        used += 1

    class BoundedSources(Sources):
        def _request(self, *args, **kwargs):
            spend()
            return super()._request(*args, **kwargs)

    class BoundedGitHub(GitHub):
        def _get(self, *args, **kwargs):
            spend()
            return super()._get(*args, **kwargs)

    sources = BoundedSources(store)
    evidence_ids = list(dict.fromkeys(source_ids))
    errors, reads, repo_origins, fulltext_count = [], [], {}, 0
    repository_groups = []
    # Explicit implementation files take precedence over heuristic README
    # discovery and share its HTTP budget. Selection is not evidence of a
    # paper-to-code relationship, so no graph edge is invented here.
    for (repo, ref, path), requested_by in pinned_requests.items():
        try:
            result = sources.code(repo, ref, path)
            evidence_ids.append(result["id"])
            reads.append({"stage": "pinned_file", "repository": repo, "commit": ref, "path": path,
                          "code": result, "requested_by": sorted(set(requested_by)),
                          "depth": "Pinned file text; implementation applicability remains unverified"})
        except Exception as error:
            errors.append({"stage": "pinned_file", "repository": repo, "commit": ref, "path": path,
                           "requested_by": sorted(set(requested_by)), "error_type": type(error).__name__})
    for doc in selected:
        origin_id = doc["id"]
        link_sources = [doc]
        identity = canonical(doc)
        if identity.startswith("arxiv:") and fulltext_count < max_fulltexts:
            fulltext_count += 1
            try:
                requested, revision_source = _arxiv_target(doc, store)
                result = sources.fetch("https://arxiv.org/abs/" + requested)
                evidence_ids.append(result["id"])
                fulltext = store.get(result["id"])
                pinned = bool(re.search(r"v\d+$", requested))
                fulltext.update(title=doc["title"], created_at=doc.get("created_at"),
                                updated_at=revision_source.get("updated_at") if pinned else None)
                fulltext["metadata"].update(canonical_paper_id=identity, requested_arxiv_id=requested,
                                             version_pinned=pinned, source_record_id=origin_id,
                                             source_record_updated_at=doc.get("updated_at"),
                                             revision_source_id=revision_source["id"])
                store.put(fulltext)
                reads.append({"source_id": origin_id, "fulltext": result, "requested_arxiv_id": requested,
                              "version_pinned": pinned, "revision_source_id": revision_source["id"]})
                link_sources.append(fulltext)
            except Exception as error:
                errors.append({"stage": "fulltext", "id": identity, "error_type": type(error).__name__})
            if citations_per_paper:
                try:
                    citations = sources.citations(identity, limit=min(5, citations_per_paper))
                    failed = bool(citations.get("error") or citations.get("errors"))
                    if failed:
                        errors.append({"stage": "citations", "id": identity, "error_type": "ProviderError"})
                    ids = citations.get("ids", [])
                    reads.append({"source_id": identity, "stage": "citations",
                                  "status": ("partial" if ids else "failed") if failed else "completed",
                                  "error_type": "ProviderError" if failed else None,
                                  "citations": {"ids": ids, "provider": citations.get("provider")},
                                  "read_depth": "not_retrieved" if failed and not ids else "bibliographic_links_only",
                                  "resolved_ids": [i for i in ids if store.get(i)],
                                  "unresolved_ids": [i for i in ids if not store.get(i)],
                                  "meaning": "Citation retrieval failed; no bibliographic coverage established." if failed and not ids else
                                      "Cited papers were not read by this expansion and are not added to reasoning evidence."})
                except Exception as error:
                    errors.append({"stage": "citations", "id": identity, "error_type": type(error).__name__})
                    reads.append({"source_id": identity, "stage": "citations", "status": "failed",
                                  "error_type": type(error).__name__, "read_depth": "not_retrieved",
                                  "meaning": "Citation retrieval failed; no bibliographic coverage established."})
        elif doc["kind"] in ("issue", "pr"):
            match = re.fullmatch(r"github:([^:]+):(\d+)", doc["id"])
            if match:
                try:
                    with contextlib.redirect_stdout(sys.stderr):
                        BoundedGitHub(store, match.group(1)).hydrate([int(match.group(2))])
                    reads.append({"source_id": doc["id"], "hydration": store.get_checkpoint("hydrated:" + match.group(1) + ":" + match.group(2))})
                except Exception as error:
                    # Individual earlier pages are already committed. No full
                    # hydration receipt is fabricated after a budget failure.
                    errors.append({"stage": "hydrate", "id": doc["id"], "error_type": type(error).__name__})
        group, group_seen = [], set()
        for link_source in link_sources:
            for candidate in _repository_links(link_source):
                repo = candidate["repository"]
                repo_origins.setdefault(repo, set()).add((origin_id, link_source["id"]))
                if repo not in group_seen:
                    group_seen.add(repo)
                    group.append({**candidate, "source_id": origin_id})
        repository_groups.append(group)
    repository_selection = _round_robin_repositories(repository_groups, max_repositories)
    for selection in repository_selection:
        repo = selection["repository"]
        try:
            gh = BoundedGitHub(store, repo)
            info, _ = gh.get("https://api.github.com/repos/" + repo)
            branch = info.get("default_branch", "main")
            head, _ = gh.get("commits/" + branch)
            # Root README is implementation discovery, not kernel verification.
            listing, _ = gh.get("contents/", {"ref": head["sha"]})
            readme = next((entry["path"] for entry in listing if entry["name"].lower() in ("readme.md", "readme.rst", "readme")), None)
            if readme:
                result = sources.code(repo, head["sha"], readme)
                evidence_ids.append(result["id"])
                reads.append({"repository": repo, "commit": head["sha"], "code": result, "selection": selection,
                              "depth": "README only; code-path qualification pending"})
                for origin, link_source_id in sorted(repo_origins[repo]):
                    store.edge(origin, "implementation_candidate", result["id"], link_source_id,
                               {"basis": "explicit repository link; applicability unverified", "link_source_id": link_source_id})
        except Exception as error:
            errors.append({"stage": "code", "repo": repo, "error_type": type(error).__name__})
    for identity in list(evidence_ids):
        evidence_ids += [r[0] for r in store.db.execute("SELECT id FROM documents WHERE parent=? ORDER BY id LIMIT 20", (identity,))]
    evidence_ids = list(dict.fromkeys(evidence_ids))
    store.db.commit()
    documents = [store.get(identity) for identity in evidence_ids]
    priorities = {"fulltext": 0, "code": 1, "diff": 2, "review": 3, "pr": 4, "issue": 4}
    reasoning_ids = [d["id"] for d in sorted(documents, key=lambda d: priorities.get(d["kind"], 5))][:20]
    write_json(out / "sources.json", documents)
    manifest = {"version": 1, "question": question, "created_at": now(), "status": "dossier_ready",
                "http_cache_misses": used, "http_limit": max_http_calls,
                "network_note": "Logical cache misses; GitHub transient retries can add HTTP attempts.",
                "reads": reads, "errors": errors,
                "reasoning_source_ids": reasoning_ids,
                "reasoning_omitted_source_ids": [identity for identity in evidence_ids if identity not in reasoning_ids],
                "repository_selection": repository_selection,
                "repository_selection_policy": "Round robin across selected sources; explicit githubRepo metadata then original source links then fulltext links. Repository names do not establish relevance or authorship.",
                "pinned_file_limit": max_code_files,
                "pinned_files_requested": len(pinned_requests),
                "sources": [{"id": d["id"], "sha256": hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest(),
                             "read_depth": d["metadata"].get("read_depth", d["kind"])} for d in documents],
                "claim_status": "source_dossier_only", "GPU_experiments": 0, "model_calls_enabled": reason}
    write_json(out / "manifest.json", manifest)
    lines = ["# Research dossier", "", question, "", "## Sources", ""]
    lines += [f"- [{d['title']}]({d['url']}) — `{d['id']}`; {d['metadata'].get('read_depth', d['kind'])}" for d in documents]
    lines += ["", "## Questions the evidence review must answer", "",
              "- What is the exact mechanism, comparator and ablation?",
              "- Which claims are author-reported, independently reproduced, upstream-implemented or locally validated?",
              "- Does the code implement the claimed method on our hardware/model path?",
              "- What time is removed, how often, and how much is exposed after accepted progress and overlap?",
              "- What is the cheapest falsifying pilot and its engineering/GPU cost?",
              "", "Discovery and fetched full text do not establish any of these conclusions."]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n")
    if reason:
        try:
            analyst = ResearchTools(store)
            packet = analyst.evidence(question, reasoning_ids, str(out / "evidence"), model=model, timeout=timeout)
            from .hypotheses import HypothesisTools
            hypotheses = HypothesisTools(store)
            try:
                rubric = hypotheses.rubric(brief_for_reasoning, str(out / "policy"), packet=packet["packet"], model=model, timeout=timeout)
                result = hypotheses.run(brief_for_reasoning, packet["packet"], str(out / "hypotheses"), rounds=1, model=model, timeout=timeout, policy=rubric["path"])
            finally:
                hypotheses.ledger.db.close()
            manifest.update(status="reasoned", evidence=packet, hypotheses=result, claim_status="reviewed_hypotheses_not_experimentally_validated")
        except Exception as error:
            manifest.update(status="reasoning_failed", reasoning_error_type=type(error).__name__)
            write_json(out / "manifest.json", manifest)
            raise
        write_json(out / "manifest.json", manifest)
    return {"output": str(out), **manifest}
