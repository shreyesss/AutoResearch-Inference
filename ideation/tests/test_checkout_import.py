"""Exercise a clean Python process: pytest's pythonpath hides artifact shadowing."""
import os
from pathlib import Path
import subprocess
import sys


def test_repo_root_imports_evidence_module_after_init():
    root = Path(__file__).resolve().parents[2]
    script = '''
import tempfile
from ideation.foundation import invoke
with tempfile.TemporaryDirectory() as d:
    invoke(['--state-dir', d, 'init'])
    from ideation.evidence import ResearchTools
    from ideation.paper_search import search_papers
    assert ResearchTools.__module__ == 'ideation.evidence'
    assert callable(search_papers)
'''
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    result = subprocess.run([sys.executable, '-c', script], cwd=root, env=env,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
