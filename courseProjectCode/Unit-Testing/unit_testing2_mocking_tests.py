"""Unit-test for ``mkdocs.commands.serve.serve``."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mkdocs.commands import serve


class ServeTests(unittest.TestCase):
    def setUp(self):
        """Create shared mock objects for each dependency module."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.site_directory = Path(self.temporary_directory.name) / "site"
        self.site_directory.mkdir()

        self.config = mock.MagicMock()
        self.config.dev_addr = ("127.0.0.1", 8000)
        self.config.site_url = None
        self.config.docs_dir = "docs"
        self.config.config_file_path = "mkdocs.yml"
        self.config.watch = []
        self.config.theme.dirs = ["theme"]
        self.config.plugins.on_serve.side_effect = lambda server, **kwargs: server

        self.server = mock.MagicMock()

        patchers = [
            mock.patch(
                "mkdocs.commands.serve.tempfile.mkdtemp",
                return_value=str(self.site_directory),
            ),
            mock.patch("mkdocs.commands.serve.shutil.rmtree"),
            mock.patch("mkdocs.commands.serve.load_config", return_value=self.config),
            mock.patch("mkdocs.commands.serve.build"),
            mock.patch(
                "mkdocs.commands.serve.LiveReloadServer", return_value=self.server
            ),
        ]
        self.mocks = [patcher.start() for patcher in patchers]
        for patcher in patchers:
            self.addCleanup(patcher.stop)

    def test_serve_starts_and_shuts_down_server(self):
        """Test that the server starts and shuts down correctly when livereload is disabled."""
        serve.serve(livereload=False, open_in_browser=False)

        self.server.serve.assert_called_once_with(open_in_browser=False)
        self.server.shutdown.assert_called_once_with()
        self.config.plugins.on_shutdown.assert_called_once_with()

    def test_serve_registers_watch_paths_when_livereload_is_enabled(self):
        """Test that the server registers the correct watch paths when livereload is enabled."""
        self.config.watch = ["extra"]

        serve.serve(livereload=True, watch_theme=True)

        watched_paths = [call.args[0] for call in self.server.watch.call_args_list]
        self.assertEqual(watched_paths, ["docs", "mkdocs.yml", "theme", "extra"])

    def test_serve_shuts_down_after_keyboard_interrupt(self):
        """Test that the server shuts down correctly after a KeyboardInterrupt."""
        self.server.serve.side_effect = KeyboardInterrupt

        serve.serve(livereload=False)

        # Assert that the server's shutdown method was called after the KeyboardInterrupt
        self.server.shutdown.assert_called_once_with()
        self.config.plugins.on_shutdown.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
