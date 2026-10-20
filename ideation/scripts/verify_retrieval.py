"""Bounded live requests followed by exact repeats; write cache evidence, no hypothesis calls."""
import json
from pathlib import Path
from ideation.store import Store, now
from ideation.toolbox import registry
from ideation.github import GitHub


def main():
    store = Store("data/corpus.sqlite")
    tools = registry(store)
    before = tools.call("research.cache_status")
    checks = []
    calls = [
        ("research.web_search", {"query": "DeepSeek B200 low batch MoE kernel performance", "limit": 5}),
        ("research.search", {"query": "MoE GEMM", "provider": "openalex", "limit": 3}),
        ("research.web_read", {"url": "https://nvidia.github.io/TensorRT-LLM/blogs/tech_blog/blog1_Pushing_Latency_Boundaries_Optimizing_DeepSeek-R1_Performance_on_NVIDIA_B200_GPUs.html", "mode": "html"}),
        ("research.read", {"url": "https://arxiv.org/html/2412.19437v1"}),
        ("research.triage", {"question": "Select up to three primary-source URLs to inspect low-batch MoE kernel dispatch and CUDA graph overhead. Explain coverage gaps; do not claim speedups.", "source_ids": ["fathom:search:f7bb3d8cfee9d699"]}),
    ]
    for name, args in calls:
        try:
            first = tools.call(name, **args)
            second = tools.call(name, **args)
            assert second["cache"]["hit"], name + " repeat did not hit cache"
            checks.append({"tool": name, "first": first, "repeat": second})
        except Exception as error:
            checks.append({"tool": name, "error_type": type(error).__name__})
    gh = GitHub(store)
    gh.get("issues/62541")
    gh.get("issues/62541")
    report = {"at": now(), "before": before, "checks": checks, "after": tools.call("research.cache_status")}
    Path("docs/cache-live-check.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"checks": [{"tool": c["tool"], "pass": "repeat" in c, "error": c.get("error_type")} for c in checks], "usage": report["after"]["budgets"]}, indent=2))
    store.db.close()


if __name__ == "__main__":
    main()
