"""Small subprocess and fixture helpers for the black-box system tests."""

import os
import socket
import subprocess
import sys
from pathlib import Path


def command_env(cwd):
    env = os.environ.copy()
    env.update(
        NO_COLOR="1",
        PYTHONIOENCODING="utf-8",
        GIT_AUTHOR_NAME="System Test",
        GIT_AUTHOR_EMAIL="system-test@example.invalid",
        GIT_COMMITTER_NAME="System Test",
        GIT_COMMITTER_EMAIL="system-test@example.invalid",
        GIT_CEILING_DIRECTORIES=str(Path(cwd).resolve().parent),
    )
    return env


def run_mkdocs(args, cwd, timeout=60):
    return subprocess.run(
        [sys.executable, "-m", "mkdocs", *args],
        cwd=cwd,
        env=command_env(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )


def write_files(root, files):
    for relpath, content in files.items():
        path = Path(root) / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def git(args, cwd):
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=command_env(cwd),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
