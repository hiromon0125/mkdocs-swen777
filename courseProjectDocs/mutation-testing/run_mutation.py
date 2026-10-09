"""Run cosmic-ray mutation testing and write the results into this folder.

Works on Windows, macOS and Linux. Run from the repository root:

    python courseProjectDocs/mutation-testing/run_mutation.py            # initial + final
    python courseProjectDocs/mutation-testing/run_mutation.py initial    # existing MkDocs tests only
    python courseProjectDocs/mutation-testing/run_mutation.py final      # existing tests + our new tests

Each team member's configuration is in courseProjectCode/mutation-testing/config/.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import TestOutcome

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / 'courseProjectCode' / 'mutation-testing' / 'config'
RESULTS_DIR = REPO_ROOT / 'courseProjectDocs' / 'mutation-testing' / 'results'

# (config name, file under test)
TARGETS = [
    ('gh_deploy', 'mkdocs/commands/gh_deploy.py'),
    ('meta', 'mkdocs/utils/meta.py'),
    ('toc', 'mkdocs/structure/toc.py'),
]

# The initial run deselects every test whose file name contains "mutation_",
# i.e. only the new tests in courseProjectCode/mutation-testing/.
PHASE_ENV = {
    'initial': {'PYTEST_ADDOPTS': '-k "not mutation_"'},
    'final': {'PYTEST_ADDOPTS': ''},
}


def cosmic_ray(*args, env):
    """Run a cosmic-ray command with the current Python interpreter."""
    subprocess.run([sys.executable, '-m', 'cosmic_ray.cli', *args], check=True, env=env, cwd=REPO_ROOT)


def cr_report(session, *flags):
    """Return the text output of cr-report for a session.

    The random "[job-id] ..." lines are dropped so re-running gives identical files.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'cosmic_ray.tools.report', *flags, str(session)],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return ''.join(line for line in result.stdout.splitlines(True) if not line.startswith('[job-id]'))


def count_results(session):
    """Return (total, killed, survived, other) for a finished session."""
    killed = survived = other = 0
    with use_db(str(session), WorkDB.Mode.open) as db:
        total = db.num_work_items
        for _, result in db.completed_work_items:
            if result.test_outcome == TestOutcome.KILLED:
                killed += 1
            elif result.test_outcome == TestOutcome.SURVIVED:
                survived += 1
            else:
                other += 1
    return total, killed, survived, other


def run_phase(phase):
    out_dir = RESULTS_DIR / phase
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, **PHASE_ENV[phase])
    
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, file in TARGETS:
            print(f'[{phase}] {file}', flush=True)
            config = CONFIG_DIR / f'{name}.toml'
            session = Path(tmp) / f'{name}.sqlite'

            cosmic_ray('init', str(config), str(session), env=env)
            cosmic_ray('baseline', str(config), env=env)  # fails if the unmutated code fails its tests
            cosmic_ray('exec', str(config), str(session), env=env)

            (out_dir / f'{name}-report.txt').write_text(cr_report(session, '--show-diff'), encoding='utf-8')
            (out_dir / f'{name}-survivors.txt').write_text(
                cr_report(session, '--show-diff', '--surviving-only'), encoding='utf-8'
            )
            rows.append((file, *count_results(session)))

    lines = [f"{'File':<32} {'Mutants':>7} {'Killed':>7} {'Survived':>9} {'Other':>6} {'Score':>8}"]
    totals = [0, 0, 0, 0]
    for file, total, killed, survived, other in rows:
        totals = [a + b for a, b in zip(totals, (total, killed, survived, other))]
        lines.append(
            f'{file:<32} {total:>7} {killed:>7} {survived:>9} {other:>6} {100 * killed / total:>7.1f}%'
        )
    total, killed, survived, other = totals
    lines.append(f"{'TOTAL':<32} {total:>7} {killed:>7} {survived:>9} {other:>6} {100 * killed / total:>7.1f}%")
    summary = '\n'.join(lines) + '\n'
    (out_dir / 'summary.txt').write_text(summary, encoding='utf-8')
    print(f'== {phase} ==\n{summary}', flush=True)


def run_new_tests():
    result = subprocess.run(
        [
            sys.executable, '-m', 'unittest', 'discover',
            '-s', 'courseProjectCode/mutation-testing', '-p', 'mutation_*_tests.py', '-v',
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    (RESULTS_DIR / 'testResults.txt').write_text(result.stderr, encoding='utf-8')
    print(result.stderr.strip().splitlines()[-1])


def main():
    phases = sys.argv[1:] or ['initial', 'final']
    for phase in phases:
        if phase not in PHASE_ENV:
            sys.exit(f'Unknown phase {phase!r}; use "initial" and/or "final".')
    for phase in phases:
        run_phase(phase)
    run_new_tests()


if __name__ == '__main__':
    main()
