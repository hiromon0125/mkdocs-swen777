"""Integration tests for the ``mkdocs gh-deploy`` command.

``mkdocs gh-deploy`` builds the site and publishes it to GitHub Pages. These
tests run the real command end to end through these modules:

    mkdocs.__main__ (click CLI)
      -> mkdocs.config (load mkdocs.yml)
      -> mkdocs.commands.build (build the site into site_dir)
      -> mkdocs.commands.gh_deploy (commit message, push, site URL)
      -> ghp_import (third-party package that pushes the site)

Only the parts that would touch git or GitHub are replaced with mocks:
ghp_import's push and gh_deploy's three small git helpers. Everything else,
including the site build, runs for real in a temporary folder.
"""

import os
import tempfile
import unittest
from unittest import mock

import ghp_import
from click.testing import CliRunner

from mkdocs.__main__ import cli
from mkdocs.commands import gh_deploy


def make_project(root):

    """Write a small two-page MkDocs project into ``root`` and return its config path."""

    docs = os.path.join(root, 'docs')

    os.makedirs(docs)

    with open(os.path.join(docs, 'index.md'), 'w', encoding='utf-8') as f:
        f.write('# Welcome\n\nIntegration test home page.\n')

    with open(os.path.join(docs, 'guide.md'), 'w', encoding='utf-8') as f:
        f.write('# Guide\n\nHow to use the project.\n')

    config_file = os.path.join(root, 'mkdocs.yml')

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('site_name: Integration Test Site\n')

    return config_file


class GhDeployCommandTests(unittest.TestCase):

    def setUp(self):

        # Creates a new empty folder in system's temporary location
        tmp = tempfile.TemporaryDirectory()
        # Deletes folder when the test finishes
        self.addCleanup(tmp.cleanup)
        # Writes mkdocs.yml and two pages to temporary location
        self.config_file = make_project(tmp.name)
        self.site_dir = os.path.join(tmp.name, 'site')

        # Replace only the parts that would run git or push to GitHub.
        for name, value in [
            ('_is_cwd_git_repo', True),
            ('_get_current_sha', 'abc1234'),
            ('_get_remote_url', ('https://', 'user/project.git')),
        ]:
            # prepares a fake for one of gh_deploy git helper functions
            patcher = mock.patch.object(gh_deploy, name, return_value=value)
            # Swaps in fake function
            patcher.start()
            # When test is finished, run patcher.stop()
            self.addCleanup(patcher.stop)

        # Swap _check_version for a fake for the test and keep a handle on the fake so the test can check whether it got called.
        self.check_version = self._start(mock.patch.object(gh_deploy, '_check_version'))
        # Swap the real "push to GitHub" function for a fake that pushes to nothing and keep a handle on it so tests can check what it was given or make it fail on purpose.
        self.ghp = self._start(mock.patch.object(gh_deploy.ghp_import, 'ghp_import'))

    def _start(self, patcher):
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_builds_site_and_passes_cli_options_to_ghp_import(self):

        """Normal case: the built site and every CLI option reach ghp-import."""

        site_at_push = {}

        def record_site(site_dir, **kwargs):

            # Look at the site folder at the moment of the push.
            site_at_push['files'] = sorted(os.listdir(site_dir))

            with open(os.path.join(site_dir, 'guide', 'index.html'), encoding='utf-8') as f:
                site_at_push['guide'] = f.read()

        # Makes the fake push run record_site whenever it's called so the test can snapshot the site folder at the moment of the push
        self.ghp.side_effect = record_site

        # Runs the mkdocs gh-deploy command and holds what happend
        result = CliRunner().invoke(
            cli,
            [
                'gh-deploy',
                '--config-file', self.config_file,
                '--remote-branch', 'docs-site',
                '--remote-name', 'upstream',
                '--message', 'Deploy {sha}',
                '--force',
                '--ignore-version',
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)

        # Checks that the fake push was called exactly once
        self.ghp.assert_called_once()

        pushed_dir = self.ghp.call_args.args[0]

        # Compare normalized paths so the test also passes on Windows.
        self.assertEqual(
            os.path.normcase(os.path.realpath(pushed_dir)),
            os.path.normcase(os.path.realpath(self.site_dir)),
        )

        # Checks that the push was given exactly these settings
        self.assertEqual(
            self.ghp.call_args.kwargs,
            {
                'mesg': 'Deploy abc1234',
                'remote': 'upstream',
                'branch': 'docs-site',
                'push': True,
                'force': True,
                'use_shell': False,
                'no_history': False,
                'nojekyll': True,
            },
        )

        # The home page wad in the site folder when it was pushed
        self.assertIn('index.html', site_at_push['files'])
        # The guide folder holds the built guide.md page was in the site folder when it was pushed
        self.assertIn('guide', site_at_push['files'])
        # Guide page contains the correct text written
        self.assertIn('How to use the project.', site_at_push['guide'])

        # --ignore-version skips the check of the last deploy's MkDocs version.
        self.check_version.assert_not_called()

    def test_push_failure_aborts_command_after_site_is_built(self):

        """Failure case: ghp-import fails, so the command exits with an error."""

        # Make the fake push raise an error, as if GitHub rejected the push
        self.ghp.side_effect = ghp_import.GhpError('remote rejected the push')

        result = CliRunner().invoke(cli, ['gh-deploy', '--config-file', self.config_file])

        self.assertEqual(result.exit_code, 1)
        self.assertIn('Deployment Aborted!', result.output)
        
        self.ghp.assert_called_once()
        # The build step finished before the push failed.
        self.assertTrue(os.path.isfile(os.path.join(self.site_dir, 'index.html')))


if __name__ == '__main__':
    unittest.main()
