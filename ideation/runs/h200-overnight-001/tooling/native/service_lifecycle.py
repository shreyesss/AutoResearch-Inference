"""Root-run bounded service lifecycle check using the existing aiohttp client.

Correctness-only requests; no service/config changes and no claim of full KV proof.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlparse


def parse_metrics(text):
    rows=[]
    pattern=re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(.*?)\})?\s+([^\s]+)')
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        match=pattern.match(line)
        if match:
            labels=dict(re.findall(r'(\w+)="([^"\\]*)"',match.group(2) or ""))
            rows.append((match.group(1),labels,float(match.group(3))))
    return rows


def drain_values(router,backends):
    expected_backends={"0","1"}
    router_gauges={labels.get("backend"):value for name,labels,value in router
                   if name=="dsv41_router_in_flight"}
    if set(router_gauges)!=expected_backends:
        raise ValueError("router in-flight series missing or unexpected")
    result={"router":router_gauges,"engines":{},"request_counts":{}}
    for name,labels,value in router:
        kind=labels.get("kind","")
        if name=="dsv41_router_requests_total" and kind.startswith("requests_backend_"):
            result["request_counts"][kind.rsplit("_",1)[1]]=value
    for replica,rows in enumerate(backends):
        for metric in ("vllm:num_requests_running","vllm:num_requests_waiting"):
            matching=[(labels,value) for name,labels,value in rows if name==metric]
            values={labels.get("engine"):value for labels,value in matching}
            if len(matching)!=4 or set(values)!={"0","1","2","3"}:
                raise ValueError(f"replica{replica} {metric}: missing/unexpected engine series")
            result["engines"][f"{replica}:{metric}"]=values
    result["zero"]=all(v==0 for v in router_gauges.values()) and all(
        v==0 for values in result["engines"].values() for v in values.values())
    return result


def session_for(replica):
    for index in range(100):
        session=f"c03-lifecycle-replica-{replica}-{index}"
        home=int.from_bytes(hashlib.sha256(session.encode()).digest()[:8],"big")%2
        if home==replica:
            return session
    raise AssertionError("no session mapping found")


async def run(args,receipt):
    import aiohttp
    urls=[args.base_url,*args.backend_urls]
    if any(urlparse(url).hostname not in ("127.0.0.1","localhost") or urlparse(url).scheme!="http" for url in urls):
        raise ValueError("this fixture is restricted to the authorized local node")
    if len(args.backend_urls)!=2 or len(set(args.backend_urls))!=2:
        raise ValueError("exactly two distinct attested backend URLs are required")
    identity=args.identity.read_bytes()
    receipt["identity_receipt"]={"path":str(args.identity),"sha256":hashlib.sha256(identity).hexdigest(),
                                 "scope":"external root runtime-attestation linkage; this client does not revalidate worker process identities"}
    timeout=aiohttp.ClientTimeout(total=180,connect=10,sock_read=60)
    async with aiohttp.ClientSession(timeout=timeout) as client:
        async def get_text(url):
            async with client.get(url) as response:
                if response.status!=200:
                    raise AssertionError(f"read-only endpoint {url} returned {response.status}")
                return await response.text()
        health=json.loads(await get_text(args.base_url+"/health"))
        if health.get("backends")!=args.backend_urls:
            raise AssertionError("router backend identity differs from attested order")
        receipt["router_health"]=health

        async def snapshot():
            text=await asyncio.wait_for(asyncio.gather(*(get_text(url+"/metrics") for url in urls)),timeout=10)
            return drain_values(parse_metrics(text[0]),[parse_metrics(s) for s in text[1:]])

        async def drain(label):
            samples=[];consecutive=0;deadline=time.monotonic()+60
            while time.monotonic()<deadline:
                try:
                    values=await asyncio.wait_for(snapshot(),timeout=min(10,deadline-time.monotonic()))
                except (asyncio.TimeoutError,ValueError) as exc:
                    receipt["drains"].append({"label":label,"status":"fail","samples":samples,
                                               "error":f"{type(exc).__name__}: {exc}"})
                    raise AssertionError(f"{label}: scrape timeout or incomplete identity/gauges") from exc
                samples.append(dict(time_unix_s=time.time(),**values))
                consecutive=consecutive+1 if values["zero"] else 0
                if consecutive==3:
                    receipt["drains"].append({"label":label,"status":"pass","samples":samples})
                    return values
                await asyncio.sleep(min(1,max(0,deadline-time.monotonic())))
            receipt["drains"].append({"label":label,"status":"fail","samples":samples})
            raise AssertionError(f"{label}: serving did not drain within60s")

        async def request(replica,label,prompt,limit,cancel=False):
            before=await snapshot()
            session_id=session_for(replica)
            body={"model":args.model,"messages":[{"role":"user","content":prompt}],
                  "stream":True,"stream_options":{"include_usage":True},
                  "temperature":0,"seed":731,"max_completion_tokens":limit,"ignore_eos":False}
            record={"replica":replica,"label":label,"session_id":session_id,"body":body,
                    "started_unix_s":time.time(),"content":"","reasoning":"","events":[],
                    "cancelled":False,"finish_reason":None,"usage":None}
            receipt["requests"].append(record)
            async with client.post(args.base_url+"/v1/chat/completions",json=body,
                                   headers={"X-Session-ID":session_id}) as response:
                record["http_status"]=response.status
                if response.status!=200:
                    record["error_body"]=await response.text()
                    raise AssertionError(f"{label}:HTTP{response.status}")
                data_lines=[];response_id=None;done=False
                async for raw in response.content:
                    line=raw.decode("utf-8").rstrip("\r\n")
                    if line.startswith("data:"):
                        data_lines.append(line[5:].strip())
                        continue
                    if line or not data_lines:
                        continue
                    data="\n".join(data_lines);data_lines=[]
                    if data=="[DONE]":
                        done=True;break
                    event=json.loads(data);record["events"].append(event)
                    if event.get("id"):
                        if response_id is None:
                            response_id=event["id"]
                        elif event["id"]!=response_id:
                            raise AssertionError("cross-request response ID within SSE stream")
                    if event.get("usage"):
                        record["usage"]=event["usage"]
                    for choice in event.get("choices",[]):
                        if choice.get("index",0)!=0:
                            raise AssertionError("unexpected completion choice")
                        delta=choice.get("delta",{})
                        record["content"]+=delta.get("content") or ""
                        record["reasoning"]+=delta.get("reasoning") or delta.get("reasoning_content") or ""
                        if choice.get("finish_reason") is not None:
                            record["finish_reason"]=choice["finish_reason"]
                    if cancel and (record["content"] or record["reasoning"]) and record["finish_reason"] is None:
                        record["cancelled"]=True;record["closed_unix_s"]=time.time()
                        response.close();break
                record["response_id"]=response_id;record["done_marker"]=done
            record["ended_unix_s"]=time.time()
            if cancel:
                if not record["cancelled"]:
                    raise AssertionError("cancellation lane did not close an unfinished content-producing request")
            elif (not done or not record["response_id"] or record["finish_reason"] not in ("stop","length")
                  or not(record["content"] or record["reasoning"])
                  or not record["usage"] or record["usage"].get("completion_tokens",0)<=0):
                raise AssertionError(f"{label}: incomplete/malformed successful completion")
            after=await drain(label+"-drain")
            deltas={str(r):after["request_counts"].get(str(r),0)-before["request_counts"].get(str(r),0) for r in range(2)}
            if deltas!={str(r):1 if r==replica else 0 for r in range(2)}:
                raise AssertionError(f"{label}: unexpected replica routing/concurrent client traffic {deltas}")
            record["observed_router_request_deltas"]=deltas
            return record

        await drain("initial")
        for replica in range(2):
            prompt=f"C03 isolated correctness marker REPLICA_{replica}. Reply with exactly the word READY."
            reference=await request(replica,"reference-before",prompt,64)
            await request(replica,"cancel-in-flight",
                          f"C03 cancellation marker REPLICA_{replica}. Write a detailed numbered list of1000different integers and explain each entry.",4096,True)
            recovery=await request(replica,"reference-after-cancel",prompt,64)
            def generated(record):
                return (record["content"],record["reasoning"],record["usage"]["completion_tokens"],record["finish_reason"])
            if generated(reference)!=generated(recovery):
                raise AssertionError("deterministic reference changed after cancellation; stop lane without tolerance")
            natural=await request(replica,"natural-stop",
                                  f"C03 natural stop marker REPLICA_{replica}. Answer only OK and finish.",512)
            wake=await request(replica,"reference-after-finished-wake",prompt,64)
            if generated(reference)!=generated(wake):
                raise AssertionError("deterministic reference changed after finished-request drain/wake")
            receipt["replicas"].append({"replica":replica,"session_id":session_for(replica),
                                        "cancel_and_observable_recovery":"pass",
                                        "finished_request_drain_and_wake":"pass",
                                        "natural_stop":"observed" if natural["finish_reason"]=="stop" else "inconclusive_at512",
                                        "exact_eos_token_id_observed":False})
    receipt["status"]="pass" if all(r["natural_stop"]=="observed" for r in receipt["replicas"]) else "inconclusive_natural_stop"


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8000")
    parser.add_argument("--backend-urls",nargs=2,default=["http://127.0.0.1:8100","http://127.0.0.1:8101"])
    parser.add_argument("--model",required=True)
    parser.add_argument("--identity",type=Path,required=True)
    parser.add_argument("--arm",choices=("A","B"),required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite lifecycle receipt")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    receipt={"schema_version":1,"arm":args.arm,"status":"running","requests":[],"drains":[],"replicas":[],
             "candidate_correctness_qualified":False,
             "scope":"bounded service completion/cancellation/drain/wake and exact controlled-output recovery; not all KV cells or targeted DP rank routing"}
    try:
        asyncio.run(run(args,receipt))
    except Exception as exc:
        receipt.update(status="fail",error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        args.output.write_text(json.dumps(receipt,indent=2)+"\n")
