"""Freeze a synthetic service mix for the direct GuideLLM study."""
import hashlib
import json
import random
from pathlib import Path

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.artifacts/optuna-direct-v1'
SHAPES = {'chat': (512, 256, 9), 'agent': (4096, 512, 4),
          'code': (2048, 512, 4), 'document': (8192, 256, 3)}
CONTEXT = {
    'chat': 'The support service accepts returns within thirty days with a receipt. Delivery takes three working days. Customers can change their shipping address before dispatch. Refunds return to the original payment method. ',
    'agent': 'The operations team handles incident tickets in priority order. Check service health, recent deployments, resource limits, and error logs before proposing a change. Record the evidence, owner, next action, and rollback procedure. Never assume that a successful health request proves all dependencies work. ',
    'code': 'def bounded_retry(operation, attempts=3):\n    last_error = None\n    for attempt in range(attempts):\n        try:\n            return operation()\n        except TimeoutError as error:\n            last_error = error\n    raise last_error\n\n',
    'document': 'The monthly service report records incoming requests, completed work, delayed tasks, and customer feedback. Capacity planning compares peak demand with staffing and infrastructure. Recommendations must distinguish measured observations from forecasts and explain uncertainty. ',
}
TASK = {
    'chat': 'Explain the available options to a customer whose order has not arrived.',
    'agent': 'Investigate elevated request latency after a deployment. Give an ordered diagnostic plan with evidence to collect and rollback criteria.',
    'code': 'Review the supplied retry implementation. Identify failure cases and propose a corrected implementation with bounded retries and tests.',
    'document': 'Summarize this report, separate observations from recommendations, and identify missing evidence for capacity planning.',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(ROOT / '.artifacts/models/Qwen3.8-27B', local_files_only=True)
    def fit(text, n):
        ids = tok.encode(text, add_special_tokens=False)
        return tok.decode((ids * (n // len(ids) + 1))[:n])
    def rendered(prefix, prompt):
        result = tok.apply_chat_template([{'role': 'system', 'content': prefix},
                                       {'role': 'user', 'content': prompt}],
                                      tokenize=True, add_generation_prompt=True,
                                      enable_thinking=False)
        return result['input_ids'] if hasattr(result, 'keys') else result
    manifests = {}
    for split in ('dev-a', 'dev-b', 'test-a', 'test-b'):
        rng = random.Random('direct-optuna-v1:' + split)
        prefixes = {c: [fit(f'Context namespace {split}/{c}/{p}. ' + CONTEXT[c], shape[0] // 2)
                        for p in range(16)] for c, shape in SHAPES.items()}
        rows = []
        blocks = 60 if split.startswith('dev') else 20
        for b in range(blocks):
            classes = [c for c, (_, _, n) in SHAPES.items() for _ in range(n)]
            rng.shuffle(classes)
            for c in classes:
                isl, osl, _ = SHAPES[c]
                p = rng.choices(range(16), weights=[1 / (k+1)**1.2 for k in range(16)])[0]
                prefix = prefixes[c][p]
                request_id = f'{split}-{len(rows):05d}-{c}'
                head = f'Request {request_id}. {TASK[c]}\nReference material:\n'
                base = len(rendered(prefix, head))
                filler = fit(CONTEXT[c], isl - base)
                for _ in range(100):
                    prompt = head + filler
                    actual = len(rendered(prefix, prompt))
                    if abs(actual - isl) <= 4:
                        break
                    ids = tok.encode(filler, add_special_tokens=False)
                    if actual > isl:
                        filler = tok.decode(ids[:len(ids) - (actual - isl)])
                    else:
                        if isl - actual > 4:
                            filler += ' a' * (isl - actual - 2)
                            continue
                        pads = [' a', ' z', '.', '!', '\n', ' Q', ' 0', ';']
                        for pad in pads:
                            delta = len(rendered(prefix, head + filler + pad)) - actual
                            if 0 < delta <= isl - actual:
                                filler += pad
                                break
                        else:
                            raise ValueError('No exact token padding available')
                assert abs(actual - isl) <= 4, (request_id, actual, isl)
                rows.append({'system_prompt': prefix, 'prompt': prompt,
                             'output_tokens_count': osl, 'request_id': request_id,
                             'request_class': c, 'expected_input_tokens': actual,
                             'target_input_tokens': isl,
                             'prefix_id': p})
        path = OUT / f'{split}.jsonl'
        path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        assert len({r['prompt'] for r in rows}) == len(rows)
        manifests[split] = {'path': str(path), 'rows': len(rows),
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        # Warm only the common prefix; measured suffixes are never warmed.
        (OUT / f'{split}-warmup.json').write_text(json.dumps([
            {'system_prompt': prefix, 'prompt': 'Warmup only. Reply OK.', 'output_tokens_count': 1}
            for c in SHAPES for prefix in prefixes[c]], indent=2))
    card = {'workload_id': 'mixed-service-shaped-v1', 'kind': 'synthetic, not production trace',
            'shapes': SHAPES, 'intentional_prefix_fraction': 0.5, 'prefix_pool_per_class': 16,
            'prefix_distribution': 'Zipf(1.2)', 'thinking': False, 'temperature': 0,
            'output_policy': 'forced exact lengths; no answer-quality claim',
            'token_count_includes_chat_template': True, 'input_target_tolerance_tokens': 4,
            'splits': manifests}
    (OUT / 'workload-card.json').write_text(json.dumps(card, indent=2))
    print(json.dumps(card, indent=2))


if __name__ == '__main__':
    main()
