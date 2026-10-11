"""Run cosmic-ray mutation testing and write the results into this folder.

Works on Windows, macOS and Linux. Run from the repository root:

    python courseProjectDocs/mutation-testing/run_mutation.py            # initial + final
    python courseProjectDocs/mutation-testing/run_mutation.py initial    # existing MkDocs tests only
    python courseProjectDocs/mutation-testing/run_mutation.py final      # existing tests + our new tests

Each team member's configuration is in courseProjectCode/mutation-testing/config/.
Exits with a non-zero code if any step fails, a run is incomplete, or a new test fails.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import TestOutcome

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / 'courseProjectCode' / 'mutation-testing' / 'config'
RESULTS_DIR = REPO_ROOT / 'courseProjectDocs' / 'mutation-testing' / 'results'
PHASES = ('initial', 'final')

# (config name, file under test)
TARGETS = [
    ('gh_deploy', 'mkdocs/commands/gh_deploy.py'),
    ('meta', 'mkdocs/utils/meta.py'),
    ('toc', 'mkdocs/structure/toc.py'),
]

# Our new test file inside a config's test-command, e.g.
# "courseProjectCode/mutation-testing/mutation_gh_deploy_tests.py".
NEW_TEST_FILE_RE = re.compile(r'\s+courseProjectCode/mutation-testing/mutation_\w+_tests\.py')


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


def config_for_phase(name, phase, tmp):
    """Return the config file to use for this phase.

    The final run uses the config as committed. The initial run uses a copy with our
    new test file removed from its test-command, so only the existing MkDocs tests run.
    """
    config = CONFIG_DIR / f'{name}.toml'
    if phase == 'final':
        return config
    text, removed = NEW_TEST_FILE_RE.subn('', config.read_text(encoding='utf-8'))
    if removed != 1:
        sys.exit(f'{config}: expected exactly one new test file in test-command, found {removed}.')
    initial_config = Path(tmp) / f'{name}-initial.toml'
    initial_config.write_text(text, encoding='utf-8')
    return initial_config


def count_results(session):
    """Return (total, killed, survived, other) for a finished session.

    "other" is any completed mutant that was neither killed nor survived
    (cosmic-ray's "incompetent" outcome). Timeouts count as killed.
    """
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


def score(killed, total):
    return 100 * killed / total if total else 0.0


def run_phase(phase):
    out_dir = RESULTS_DIR / phase
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    # Make sure "python" in the test-command is this same interpreter.
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, file in TARGETS:
            print(f'[{phase}] {file}', flush=True)
            config = config_for_phase(name, phase, tmp)
            session = Path(tmp) / f'{name}.sqlite'

            cosmic_ray('init', str(config), str(session), env=env)
            cosmic_ray('baseline', str(config), env=env)  # fails if the unmutated code fails its tests
            cosmic_ray('exec', str(config), str(session), env=env)

            total, killed, survived, other = count_results(session)
            if killed + survived + other != total:
                sys.exit(
                    f'[{phase}] {file}: only {killed + survived + other} of {total} mutants finished. '
                    'Results are incomplete and were not written.'
                )

            (out_dir / f'{name}-report.txt').write_text(cr_report(session, '--show-diff'), encoding='utf-8')
            (out_dir / f'{name}-survivors.txt').write_text(
                cr_report(session, '--show-diff', '--surviving-only'), encoding='utf-8'
            )
            rows.append((file, total, killed, survived, other))

    lines = [f"{'File':<32} {'Mutants':>7} {'Killed':>7} {'Survived':>9} {'Other':>6} {'Score':>8}"]
    totals = [0, 0, 0, 0]
    for file, total, killed, survived, other in rows:
        totals = [a + b for a, b in zip(totals, (total, killed, survived, other))]
        lines.append(f'{file:<32} {total:>7} {killed:>7} {survived:>9} {other:>6} {score(killed, total):>7.1f}%')
    total, killed, survived, other = totals
    lines.append(f"{'TOTAL':<32} {total:>7} {killed:>7} {survived:>9} {other:>6} {score(killed, total):>7.1f}%")
    summary = '\n'.join(lines) + '\n'
    (out_dir / 'summary.txt').write_text(summary, encoding='utf-8')
    print(f'== {phase} ==\n{summary}', flush=True)


def run_new_tests():
    """Run our new tests, save the output, and return unittest's exit code."""
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
    lines = result.stderr.strip().splitlines()
    print(lines[-1] if lines else f'unittest produced no output (exit code {result.returncode})')
    return result.returncode


def main():
    phases = sys.argv[1:] or list(PHASES)
    for phase in phases:
        if phase not in PHASES:
            sys.exit(f'Unknown phase {phase!r}; use "initial" and/or "final".')
    for phase in phases:
        run_phase(phase)
    # testResults.txt records the new tests, which only belong to the final run.
    if 'final' in phases:
        sys.exit(run_new_tests())


if __name__ == '__main__':
    main()
