"""Mutation-testing tests for ``mkdocs/commands/gh_deploy.py``

``gh_deploy.py`` is the code behind the ``mkdocs gh-deploy`` command, which
builds the site and publishes it to GitHub Pages.

The existing ``gh_deploy_tests.py`` mocks ``subprocess.Popen`` and
``ghp_import`` but mostly checks return values. It never checks *how*
ghp-import is called, never tests version-comparison boundaries, and never
checks the GitHub Pages URL that is printed, so many mutants survived.
"""

import os
import tempfile
import unittest
from unittest import mock

import mkdocs
from mkdocs.commands import gh_deploy

LOGGER = 'mkdocs.commands.gh_deploy'
PREFIX = f'{LOGGER}:'


def _fake_popen(stdout=b''):
    """Build a Popen mock whose process prints the given output."""
    popen = mock.MagicMock()
    popen.return_value.communicate.return_value = (stdout, b'')
    return popen


@mock.patch.object(mkdocs, '__version__', '2.0.0')
class CheckVersionTests(unittest.TestCase):
    """``_check_version`` compares the MkDocs version recorded in the last gh-pages
deploy commit with the MkDocs version running now."""

    def _run(self, commit_message):
        # Temporarily replaces subprocess.Popen (The function gh_deploy.py uses to run git), with a fake
        # that returns commit_message as git's output
        # Then runs check version on gh-pages branch because that is where gh-deploy publishes your site
        with mock.patch.object(gh_deploy.subprocess, 'Popen', _fake_popen(commit_message.encode())):
            gh_deploy._check_version('gh-pages')

    def test_same_version_logs_nothing_and_does_not_abort(self):
        """Deploying the same version is neither an upgrade nor a downgrade.

        Kills the mutants that turn ``>`` into ``>=`` (would log an upgrade)
        and ``<`` into ``<=`` or ``is not`` (would abort).
        """
        with self.assertNoLogs(LOGGER, level='DEBUG'):
            self._run('Deployed abc with MkDocs version: 2.0.0')

    def test_uppercase_prerelease_is_parsed_case_insensitively(self):
        """``2.0.0RC1`` must be read as ``2.0.0rc1``, which is older than ``2.0.0``.

        Kills the mutants that replace ``re.X | re.I`` with another operator
        and lose the case-insensitive flag, so only ``2.0.0`` is matched.
        """
        with self.assertLogs(LOGGER, level='INFO') as logs:
            self._run('Deployed abc with MkDocs version: 2.0.0RC1')

        self.assertEqual(
            logs.output,
            [
                f'INFO:{PREFIX}Previous deployment was done with MkDocs version 2.0.0rc1; '
                'you are deploying with a newer version (2.0.0)'
            ],
        )


class GhDeployTests(unittest.TestCase):
    """``gh_deploy()`` with git, ghp-import and the helpers replaced by mocks."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.site_dir = tmp.name

        self.config = mock.MagicMock()
        self.config.site_dir = self.site_dir
        self.config.remote_branch = 'gh-pages'
        self.config.remote_name = 'origin'
        self.config.config_file_path = os.path.join('/project', 'mkdocs.yml')

        self.check_version = self._patch('_check_version')
        self.get_sha = self._patch('_get_current_sha', return_value='abc1234')
        self.get_remote = self._patch('_get_remote_url', return_value=('https://', 'user/project.git'))
        self._patch('_is_cwd_git_repo', return_value=True)
        patcher = mock.patch.object(gh_deploy.ghp_import, 'ghp_import')
        self.ghp = patcher.start()
        self.addCleanup(patcher.stop)

    def _patch(self, name, **kwargs):
        """Replace ``gh_deploy.<name>`` with a mock for the whole test and restore it afterwards."""
        patcher = mock.patch.object(gh_deploy, name, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_default_arguments_are_passed_to_ghp_import(self):
        """Checks every argument passed to ghp-import and the printed Pages URL.

            Kills the mutants that flip one of ghp-import's options (``push``,
            ``nojekyll``, ``force``, ``no_history``, ``use_shell``), and the mutants in
            ``gh_deploy()``'s own URL logic that change the ``host is None`` check or
            break the ``.git`` suffix removal.
            """
        
        with self.assertLogs(LOGGER, level='INFO') as logs:
            gh_deploy.gh_deploy(self.config)

        self.ghp.assert_called_once_with(
            self.site_dir,
            mesg=f'Deployed abc1234 with MkDocs version: {mkdocs.__version__}',
            remote='origin',
            branch='gh-pages',
            push=True,
            force=False,
            use_shell=False,
            no_history=False,
            nojekyll=True,
        )
        self.check_version.assert_called_once_with('gh-pages')
        self.get_sha.assert_called_once_with('/project')
        self.get_remote.assert_called_once_with('origin')
        self.assertEqual(
            logs.output,
            [
                f"INFO:{PREFIX}Copying '{self.site_dir}' to 'gh-pages' branch and pushing to GitHub.",
                f'INFO:{PREFIX}Your documentation should shortly be available at: '
                'https://user.github.io/project/',
            ],
        )


if __name__ == '__main__':
    unittest.main()
