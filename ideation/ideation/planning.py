"""Natural-language control to an editable search plan; no automatic search fan-out."""
import json
from pathlib import Path

from .evidence import new_output, write_json
from .research import S, arr, obj, run_agent

PLAN = obj({"question": S, "scope": S, "excluded": arr(S), "selected_topics": arr(S),
            "github_queries": arr(obj({"query": S, "match": {"type": "string", "enum": ["all", "any"]}, "purpose": S})),
            "paper_queries": arr(S), "web_queries": arr(S), "read_next": arr(S), "stop_when": S})


class PlanningTools:
    def topics(self, ids=None):
        """User-supplied detailed vocabulary. Omit ids for topic names; pass IDs for terms."""
        guide = json.loads((Path(__file__).resolve().parents[1] / "config/keyword-guide.json").read_text())
        return [t if ids else {"id": t["id"], "name": t["name"], "terms": len(t["terms"])}
                for t in guide["topics"] if not ids or t["id"] in ids]

    def plan(self, instructions, output, topic_ids=None, repos=None, after=None, count=2, model=None, require_novelty=None):
        """Turn any user direction into an editable bounded plan. Does not execute searches."""
        import jsonschema
        if not instructions.strip():
            raise ValueError("Provide your research direction")
        if require_novelty is not None and not isinstance(require_novelty, bool):
            raise ValueError("require_novelty must be boolean")
        repos = ["vllm-project/vllm"] if repos is None else repos
        out = new_output(output)
        prompt = ("Create an engineering search plan from the user's instructions. They control domain, specificity, inclusions and exclusions. "
                  "The supplied vocabulary is a guide, not a requirement or verified technical fact. Do not force DeepSeek/B200 or speculation if not requested. "
                  "Use at most 8 GitHub queries, 4 paper queries and 2 web queries. Use precise identifiers and 2–4 term intersections for narrow queries, "
                  "plus a broader mechanism query and counterevidence/failure query. Do not put the entire taxonomy into a query. "
                  "GitHub query syntax is literal phrases with all/any; no GitHub site-search operators. "
                  "Do not invent source URLs. Web queries are optional, only for coverage gaps. State what to inspect and when to stop.\n" +
                  json.dumps({"instructions": instructions, "repos": repos, "after": after, "vocabulary": self.topics(topic_ids)}))
        result = run_agent(prompt, PLAN, out, "plan", model, 180,
                           "You plan retrieval. Do not call tools, read files, or spawn agents. Return only the schema.")
        jsonschema.validate(result, PLAN)
        if len(result["github_queries"]) > 8 or len(result["paper_queries"]) > 4 or len(result["web_queries"]) > 2:
            raise ValueError("Plan exceeds query bounds; inspect saved output")
        result.update(instructions=instructions, repos=repos, after=after,
                      count=min(5, max(1, int(count))), date_field="updated_at", execute_web=False)
        write_json(out / "plan.json", result)
        write_json(out / "brief.json", {"name": result["scope"], "instructions": instructions, "focus": result["question"],
                   "repos": repos, "count": result["count"], "after": after, "excluded": result["excluded"],
                   "selection": {} if require_novelty is None else {"require_novelty": require_novelty},
                   "constraints": ["No GPU execution", "No invented measured bottleneck or speedup", "Follow user-specified scope"]})
        return {"plan": str(out / "plan.json"), "brief": str(out / "brief.json"), "searches_executed": 0, "content": result}
