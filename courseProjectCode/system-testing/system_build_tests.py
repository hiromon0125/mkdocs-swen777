"""Project creation and build workflows through the public CLI."""

import re
import tempfile
import unittest
from pathlib import Path

from system_support import run_mkdocs, write_files


class BuildSystemTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_st_b1_create_and_build(self):
        """ST-B1: Create a project, build it, and inspect the published files."""
        result = run_mkdocs(["new", "proj"], self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        project = self.root / "proj"
        self.assertIn("site_name: My Docs", (project / "mkdocs.yml").read_text(encoding="utf-8"))
        self.assertTrue((project / "docs/index.md").is_file())

        write_files(project, {
            "mkdocs.yml": "site_name: System Test Site\n",
            "docs/index.md": "# Home\n\n[About](about.md)\n",
            "docs/about.md": "# About\n",
        })
        result = run_mkdocs(["build", "-d", "out"], project)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = project / "out"
        for filename in ("index.html", "about/index.html", "sitemap.xml", "404.html"):
            with self.subTest(filename=filename):
                self.assertTrue((output / filename).is_file(), filename)
        html = (output / "index.html").read_text(encoding="utf-8")
        self.assertRegex(html, re.compile(r"<title>[^<]*System Test Site[^<]*</title>"))
        self.assertIn('href="about/"', html)

    def test_st_b2_strict_broken_link(self):
        """ST-B2: A broken link warns normally and fails in strict mode."""
        write_files(self.root, {
            "mkdocs.yml": "site_name: Broken Link Test\n",
            "docs/index.md": "# Home\n\n[Missing](missing.md)\n",
        })
        result = run_mkdocs(["build"], self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING", result.stderr)
        self.assertIn("missing.md", result.stderr)

        result = run_mkdocs(["build", "--strict"], self.root)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("WARNING", result.stderr)
        self.assertIn("missing.md", result.stderr)
        self.assertRegex(result.stdout, r"Aborted with \d+ warnings? in strict mode!")

    def test_st_b3_missing_config(self):
        """ST-B3: Building in an empty directory reports the missing config."""
        result = run_mkdocs(["build"], self.root)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Config file 'mkdocs.yml' does not exist.", result.stderr)


if __name__ == "__main__":
    unittest.main()
