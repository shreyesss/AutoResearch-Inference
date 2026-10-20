import json
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .store import ALIASES, Store

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Inference research workbench</title>
<style>body{font:15px system-ui;margin:0;background:#f4f5f7;color:#182235}header{background:#14253a;color:white;padding:24px 5%}main{margin:24px 5%;max-width:1500px}h1{margin:0;font-size:26px}h2{font-size:18px}input,select,button{font:inherit;padding:9px;border:1px solid #c3cbd5;border-radius:5px}button{background:#1859a9;color:white;cursor:pointer}form{display:flex;gap:9px;flex-wrap:wrap;align-items:center}#q{flex:1;min-width:240px}.filters{margin:12px 0}.muted{color:#5b687a;font-size:13px}.card{background:white;border:1px solid #d9dfe6;padding:18px;border-radius:8px;margin:12px 0}a{color:#12549c}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px ui-monospace,monospace}.tag{display:inline-block;padding:3px 7px;background:#e9eff7;border-radius:4px;margin:3px;font-size:12px}.grid{display:grid;grid-template-columns:minmax(400px,1fr) minmax(300px,.8fr);gap:24px}#detail{position:sticky;top:15px;max-height:85vh;overflow:auto}.small{font-size:12px}label{display:flex;align-items:center;gap:5px}details{margin-top:10px}#summary{margin:14px 0} @media(max-width:900px){.grid{display:block}#detail{position:static;max-height:none}}</style></head>
<body><header><h1>Inference research workbench</h1><p>vLLM issues, PRs, papers, and evidence for testable hypotheses</p><a style="color:#b8d6ff" href="/runs">Browse research runs and hypotheses →</a></header><main>
<div id="status" class="muted">Loading corpus status…</div><form id="search"><input id="q" placeholder="perf, TTFT, TPOT, speculation…" value="deepseek-v4.1-flash b200"><select id="match"><option value="any">Any term</option><option value="all">All terms</option></select><button>Search</button></form>
<div class="filters"><label>After (inclusive) <input id="after" type="date" value="2026-01-01"> Before (exclusive) <input id="before" type="date"> <select id="date_field"><option>updated_at</option><option>created_at</option><option>merged_at</option></select></label></div>
<form class="filters"><select id="kind"><option value="">All source types</option><option>issue</option><option>pr</option><option>comment</option><option>review</option><option>review_comment</option><option>diff</option><option>paper</option><option>fulltext</option></select><select id="state"><option value="">All states</option><option>open</option><option>closed</option><option>merged</option></select><select id="gpu"><option value="">Any GPU</option><option>b200</option><option>h100</option></select><select id="model"><option value="">Any model/architecture</option><option>deepseek-v4.1-flash</option><option>deepseek</option><option>moe</option><option>mla</option></select><select id="metric"><option value="">Any metric</option><option>ttft</option><option>tpot</option><option>throughput</option><option>performance</option></select><select id="sort"><option value="relevance">Relevance</option><option value="newest">Newest</option></select></form>
<div id="summary" class="muted"></div><div class="grid"><section id="results"></section><section><div id="detail" class="card">Select a source to inspect provenance and its graph connections.</div></section></div></main>
<script>
const $=id=>document.getElementById(id); const node=(tag,text,cls)=>{let n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n};
async function api(path){let r=await fetch(path);let x=await r.json();if(!r.ok)throw Error(x.error);return x}
async function status(){let x=await api('/api/status');let cp=Object.entries(x.checkpoints).filter(([k,v])=>k.startsWith('vllm-project'));$('status').textContent=x.documents.toLocaleString()+' source records · '+x.edges.toLocaleString()+' graph edges · '+cp.map(([k,v])=>k.split(':')[1]+': '+(v.completed_at?'last full pass '+v.completed_at:'backfill page '+v.page)+(v.in_progress?' (running/incomplete)':'')).join(' · ')}
async function inspect(id){let x=await api('/api/source?id='+encodeURIComponent(id));let box=$('detail');box.replaceChildren(node('h2',x.title),node('p',x.id,'small'),node('pre',JSON.stringify({state:x.state,created:x.created_at,updated:x.updated_at,fetched:x.fetched_at,metadata:x.metadata},null,2)),node('h2','Source text'),node('pre',x.body));let edges=await api('/api/graph?node='+encodeURIComponent(id));box.append(node('h2','Graph: explicit links, mentions, and attributed claims'));for(let e of edges){box.append(node('pre',e.relation+' → '+e.dst+'\n'+e.detail))}}
async function search(){let p=new URLSearchParams();for(let k of ['q','match','after','before','date_field','kind','state','sort'])if($(k).value)p.set(k,$(k).value);for(let k of ['gpu','model','metric'])if($(k).value)p.append('tag',$(k).value);p.set('limit','50');let start=performance.now();try{let rows=await api('/api/search?'+p);$('results').replaceChildren();$('summary').textContent=rows.length+' results (up to 50) · '+Math.round(performance.now()-start)+' ms. Date filters apply to the selected source record; comments have their own dates.';for(let x of rows){let c=node('article','','card');let title=node('a',x.title);title.href=x.url;title.target='_blank';title.rel='noopener';c.append(title,node('p',x.kind+' · '+(x.state||'')+' · updated '+(x.updated_at||'unknown'),'muted'));for(let t of x.tags)c.append(node('span',t,'tag'));if(x.metadata.base)c.append(node('p','Target branch: '+x.metadata.base.ref+' · '+(x.metadata.base.sha||'').slice(0,12),'small'));c.append(node('p','BM25 '+Number(x.rank).toFixed(4)+' · lower is better; dates filter eligibility','small'));c.append(node('p',x.body.slice(0,360)));let b=node('button','Inspect evidence');b.onclick=()=>inspect(x.id);c.append(b);$('results').append(c)}}catch(e){$('summary').textContent=e.message}}
$('search').onsubmit=e=>{e.preventDefault();search()};document.querySelectorAll('select,input[type=date]').forEach(x=>x.onchange=search);const initial=new URLSearchParams(location.search);for(const k of ['q','match','after','before','date_field','kind','state','sort'])if(initial.has(k))$(k).value=initial.get(k);status();search();setInterval(status,30000);
</script></body></html>"""

def serve(db, host="127.0.0.1", port=8765):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            one = lambda key, default=None: params.get(key, [default])[0]
            store = Store(db)
            try:
                if parsed.path == "/":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(PAGE.encode())
                    return
                if parsed.path == "/runs":
                    name = one("name")
                    root = Path("runs").resolve()
                    content = '<h1>Research runs</h1><p><a href="/">← Search corpus</a></p>'
                    if name:
                        run = (root / name).resolve()
                        if run.parent != root or not run.is_dir():
                            raise ValueError("Unknown run")
                        manifest = run / "manifest.json"
                        decision = run / "decision.md"
                        content += "<h2>" + html.escape(name) + "</h2><pre>" + html.escape(manifest.read_text() if manifest.exists() else "No manifest") + "</pre>"
                        content += "<pre>" + html.escape(decision.read_text() if decision.exists() else "Research is incomplete; no final shortlist yet.") + "</pre>"
                    else:
                        for path in sorted(root.glob("*/manifest.json"), reverse=True):
                            data = json.loads(path.read_text())
                            name = path.parent.name
                            content += '<p><a href="/runs?name=' + html.escape(name, quote=True) + '">' + html.escape(name) + "</a> — " + html.escape(data.get("status", "unknown")) + " — " + str(data.get("hypotheses", "pending")) + " hypotheses</p>"
                    body = '<!doctype html><meta charset="utf-8"><title>Research runs</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#182235}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f5f7;padding:20px;font:14px ui-monospace,monospace}a{color:#12549c}</style>' + content
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(body.encode())
                    return
                if parsed.path == "/api/status":
                    result = store.stats()
                elif parsed.path == "/api/search":
                    result = store.search(query=one("q", ""), match=one("match", "any"), after=one("after"), before=one("before"), date_field=one("date_field", "updated_at"), kind=one("kind"), state=one("state"), tags=params.get("tag"), sort=one("sort", "relevance"), limit=int(one("limit", "20")))
                elif parsed.path == "/api/source":
                    result = store.get(one("id", ""))
                elif parsed.path == "/api/graph":
                    result = store.graph(one("node", ""))
                else:
                    self.reply({"error": "Not found"}, 404)
                    return
                self.reply(result)
            except Exception as e:
                self.reply({"error": str(e)}, 400)
            finally:
                store.db.close()

        def reply(self, data, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    print(f"Workbench: http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
