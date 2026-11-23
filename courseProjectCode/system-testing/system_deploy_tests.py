"""Publishing workflows through the public CLI and a local Git remote."""

import shutil
import tempfile
import unittest
from pathlib import Path

from system_support import git, run_mkdocs, write_files


@unittest.skipUnless(shutil.which("git"), "git must be on PATH")
class DeploySystemTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root / "proj"
        write_files(self.project, {
            "mkdocs.yml": "site_name: Deploy Test Site\n",
            "docs/index.md": "# Deployment\n",
        })

    def test_st_d1_deploy_to_gh_pages(self):
        """ST-D1: Push generated pages and source commit metadata to a local remote."""
        remote = self.root / "remote.git"
        git(["init", "--bare", str(remote)], self.root)
        git(["init"], self.project)
        git(["add", "-A"], self.project)
        git(["commit", "-m", "init"], self.project)
        git(["remote", "add", "origin", str(remote.resolve())], self.project)
        source_sha = git(["rev-parse", "HEAD"], self.project).stdout.strip()

        result = run_mkdocs(["gh-deploy"], self.project)
        self.assertEqual(result.returncode, 0, result.stderr)
        files = git(
            ["--git-dir", str(remote), "ls-tree", "-r", "--name-only", "gh-pages"],
            self.root,
        ).stdout.splitlines()
        self.assertIn("index.html", files)
        self.assertIn(".nojekyll", files)
        message = git(
            ["--git-dir", str(remote), "log", "-1", "--format=%s", "gh-pages"],
            self.root,
        ).stdout.strip()
        self.assertTrue(message.startswith("Deployed "), message)
        self.assertIn("with MkDocs version:", message)
        deployed_sha = git(["rev-parse", message.split()[1]], self.project).stdout.strip()
        self.assertEqual(deployed_sha, source_sha)

    def test_st_d2_deploy_outside_git_repo(self):
        """ST-D2: A failed deploy outside Git leaves the already built site behind."""
        result = run_mkdocs(["gh-deploy"], self.project)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "Cannot deploy - this directory does not appear to be a git repository",
            result.stderr,
        )
        self.assertIn("Deployment Aborted!", result.stdout)
        self.assertTrue((self.project / "site/index.html").is_file())


if __name__ == "__main__":
    unittest.main()
