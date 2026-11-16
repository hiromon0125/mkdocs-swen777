"""Live preview workflows through a subprocess and loopback HTTP."""

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from system_support import command_env, free_port, run_mkdocs, write_files


class ServeSystemTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        write_files(self.root, {
            "mkdocs.yml": "site_name: Serve Test Site\n",
            "docs/index.md": "# Home\n\n[About](about.md)\n",
            "docs/about.md": "# About\n",
        })

    @staticmethod
    def stop_server(process):
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)

    def interrupt_server(self, process):
        if process.poll() is not None:
            return
        if os.name == "nt":
            # Windows Popen cannot deliver POSIX SIGINT to this child.
            self.stop_server(process)
            return
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.stop_server(process)

    def test_st_s1_serve_over_http(self):
        """ST-S1: Serve the homepage, a subpage, and a missing URL."""
        port = free_port()
        log_path = self.root / "serve.log"
        log = log_path.open("w", encoding="utf-8")
        self.addCleanup(log.close)
        process = subprocess.Popen(
            [sys.executable, "-m", "mkdocs", "serve", "-a", f"127.0.0.1:{port}",
             "--no-livereload"],
            cwd=self.root,
            env=command_env(self.root),
            stdout=log,
            stderr=log,
        )
        self.addCleanup(self.stop_server, process)
        # SIGINT lets MkDocs remove its preview directory even if an assertion fails.
        self.addCleanup(self.interrupt_server, process)
        base_url = f"http://127.0.0.1:{port}"
        # Ignore HTTP proxy settings for requests to this local test server.
        http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                self.fail("serve exited before readiness:\n" + log_path.read_text(encoding="utf-8"))
            try:
                with http.open(base_url + "/", timeout=1) as response:
                    status = response.status
                    body = response.read().decode("utf-8")
                break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.1)
        else:
            self.fail("serve did not become ready within 30 seconds:\n"
                      + log_path.read_text(encoding="utf-8"))

        self.assertEqual(status, 200)
        self.assertIn("Serve Test Site", body)
        with http.open(base_url + "/about/", timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("About", response.read().decode("utf-8"))
        with self.assertRaises(urllib.error.HTTPError) as missing:
            http.open(base_url + "/does-not-exist/", timeout=5)
        self.addCleanup(missing.exception.close)
        self.assertEqual(missing.exception.code, 404)
        self.assertFalse((self.root / "site").exists())

        self.interrupt_server(process)

    def test_st_s2_invalid_dev_address(self):
        """ST-S2: Reject a dev address that is not IP:PORT."""
        result = run_mkdocs(["serve", "-a", "notanaddress"], self.root, timeout=30)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn("Must be a string of format 'IP:PORT'", result.stderr)


if __name__ == "__main__":
    unittest.main()
