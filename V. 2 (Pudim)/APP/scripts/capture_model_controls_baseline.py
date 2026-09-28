"""Explicit, non-overwriting baseline capture from the audited commit only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import platform
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
sys.path.insert(0, str(APP))
sys.path.insert(0, str(APP / 'tests'))

from golden_model_support import BASE_COMMIT, CASES, capture_case, sha256, write_json


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf8').strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New empty directory; existing baselines are never overwritten.')
    args = parser.parse_args()
    if git('rev-parse', 'HEAD') != BASE_COMMIT:
        parser.error('Capture must run at the audited base commit, not after new rules.')
    if git('diff', BASE_COMMIT, '--', 'V. 2 (Pudim)/APP/app_front', 'requirements.txt'):
        parser.error('Production differs from the audited commit; refusing baseline update.')
    if args.output.exists():
        parser.error('Output already exists; inspect it rather than overwrite a golden baseline.')
    versions = {}
    for name in ('numpy', 'pandas', 'scipy', 'scikit-learn', 'pydantic', 'openpyxl',
                 'SQLAlchemy', 'streamlit', 'xhtml2pdf', 'reportlab', 'pypdf'):
        versions[name] = importlib.metadata.version(name)
    sources = {}
    prefix = 'V. 2 (Pudim)/APP/app_front'
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', prefix, 'requirements.txt'], cwd=ROOT)
    for name in tracked.decode('utf8').split('\0'):
        if name and (name.endswith(('.py', '.md')) or name == 'requirements.txt'):
            # Stable text artifact digest across Git LF/CRLF checkouts.
            content = (ROOT / name).read_bytes().replace(b'\r\n', b'\n')
            sources[name] = hashlib.sha256(content).hexdigest()
    args.output.mkdir(parents=True)
    manifest = {'baseline_version': '1.0', 'source_commit': BASE_COMMIT,
                'captured_at_utc': datetime.now(timezone.utc).isoformat(),
                'python': platform.python_version(), 'platform': platform.platform(),
                'libraries': versions, 'source_sha256_normalized_lf': sources,
                'float_comparison': {'relative': 1e-10, 'absolute': 1e-10},
                'scope': 'Test-only baseline; not a production reproduction_manifest implementation.',
                'cases': {}}
    for name in CASES:
        snapshot = capture_case(name)
        path = args.output / f'{name}.json'
        write_json(path, snapshot)
        manifest['cases'][name] = {'snapshot': path.name, 'sha256': sha256(path),
                                   'input': snapshot['input'], 'execution': snapshot['execution']}
        print(name, snapshot['output']['finscore_observado']['finscore_prudencial'],
              snapshot['policy']['decisao'], flush=True)
    write_json(args.output / 'manifest.json', manifest)


if __name__ == '__main__':
    main()
