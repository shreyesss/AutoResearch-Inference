#!/usr/bin/env python3
"""Create observation-only copies; never edit the pinned originals."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / 'c03/source/base'
OUT = ROOT / 'source/observation'
FILES = ['vllm/v1/worker/gpu/model_runner.py',
         'vllm/v1/worker/gpu/spec_decode/dflash/speculator.py']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def scope(text, begin, end, name):
    assert text.count(begin) == 1
    a = text.index(begin)
    b = text.index(end, a)
    block = text[a:b]
    indent = len(begin) - len(begin.lstrip())
    return text[:a] + ' ' * indent + f'with torch.profiler.record_function("{name}"):\n' + ''.join('    ' + line if line.strip() else line for line in block.splitlines(True)) + text[b:]


class StripScopes(ast.NodeTransformer):
    def visit_With(self, node):
        self.generic_visit(node)
        if len(node.items) == 1:
            call = node.items[0].context_expr
            if isinstance(call, ast.Call) and ast.unparse(call.func) == 'torch.profiler.record_function' and len(call.args) == 1 and isinstance(call.args[0], ast.Constant) and str(call.args[0].value).startswith('avk5.'):
                assert not call.keywords and node.items[0].optional_vars is None
                return node.body
        return node


def main():
    entries = []
    for relative in FILES:
        original = (BASE / relative).read_bytes()
        text = original.decode()
        if relative.endswith('model_runner.py'):
            text = scope(text, '        # Run model.\n', '        self.kv_connector.finish_forward()\n', 'avk5.target_forward')
        else:
            begin = '        if batch_desc.cg_mode == CUDAGraphMode.FULL:\n            assert self.query_cudagraph_manager is not None\n'
            text = scope(text, begin, '        return self.draft_tokens[:num_reqs]\n', 'avk5.draft_execution')
            tree = ast.parse(text)
            methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'propose']
            assert len(methods) == 1
            method = methods[0]
            lines = text.splitlines(True)
            start, end = method.body[0].lineno - 1, method.end_lineno
            lines[start:end] = ['        with torch.profiler.record_function("avk5.draft_propose"):\n'] + [('    ' + line if line.strip() else line) for line in lines[start:end]]
            text = ''.join(lines)
        observed_tree = StripScopes().visit(ast.parse(text))
        assert ast.dump(observed_tree, include_attributes=False) == ast.dump(ast.parse(original), include_attributes=False), relative
        output = OUT / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)
        entries.append({'path': relative, 'source': str(output.relative_to(ROOT)), 'sha256': sha(text.encode()), 'base_sha256': sha(original), 'ast_only_added_record_function_scopes': True})
    manifest = {'schema_version': 1, 'purpose': 'AV-OFF k5 timing observation only; original baseline semantics', 'image': 'vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c', 'files': entries, 'scopes': {'avk5.target_forward': 'Target forward branch including connector pre_forward; host range is not GPU duration', 'avk5.draft_propose': 'Entire DFlash propose including input preparation, dispatch, context, execution and sampling', 'avk5.draft_execution': 'FULL graph composite includes context/model/sampling; eager path generate_draft includes model/sampling'}, 'prohibited_inference': ['CPU duration as GPU duration', 'FULL draft composite as pure draft model time', 'occupied GPU duration as exposed critical-path delay']}
    (ROOT / 'observation-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
