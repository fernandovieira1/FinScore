"""Run existing unittest suite and/or the added golden corpus from any cwd."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
sys.path.insert(0, str(APP.parent))  # existing APP.tests fixture imports


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('legacy', 'golden', 'all'), default='all')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    discovered = unittest.defaultTestLoader.discover(str(APP / 'tests'), pattern='test_*.py')
    selected = []
    for test in cases(discovered):
        is_golden = 'test_model_controls_golden.' in test.id()
        if args.suite == 'all' or is_golden == (args.suite == 'golden'):
            selected.append(test)
    if not selected:
        parser.error('No tests selected.')
    args.output.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with (args.output / f'{args.suite}.log').open('w', encoding='utf8') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.TestSuite(selected))
    summary = {'suite': args.suite, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'run': result.testsRun, 'failures': len(result.failures),
               'errors': len(result.errors), 'skipped': len(result.skipped),
               'seconds': round(time.monotonic() - start, 3),
               'failed_ids': [test.id() for test, _ in result.failures + result.errors]}
    (args.output / f'{args.suite}.json').write_text(
        json.dumps(summary, indent=2) + '\n', encoding='utf8')
    print(json.dumps(summary))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
